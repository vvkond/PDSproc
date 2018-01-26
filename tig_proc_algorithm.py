# -*- coding: utf-8 -*-


__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from PyQt4.QtCore import QSettings, QProcess, QVariant
from qgis.utils import iface
from qgis.core import *

import processing
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.parameters import ParameterNumber
from processing.core.outputs import OutputRaster
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter
from processing.tools.system import getTempFilename


class TigSurfitAlgorithm(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FAULT = 'INPUT_FAULT'
    INPUT_FIELD = 'INPUT_FIELD'
    STEP_X_VALUE = 'STEP_X'
    STEP_Y_VALUE = 'STEP_Y'
    EXPAND_PERCENT_X = 'EXPAND_PERCENT_X'
    EXPAND_PERCENT_Y = 'EXPAND_PERCENT_Y'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = self.tr('Create grid with faults')

        # The branch of the toolbox under which the algorithm will appear
        self.group = u'Grids'

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterVector(self.INPUT_LAYER,
            self.tr('Input points'), [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterTableField(self.INPUT_FIELD, self.tr('Field name'),
            self.INPUT_LAYER, ParameterTableField.DATA_TYPE_NUMBER))

        self.addParameter(ParameterVector(self.INPUT_FAULT,
            self.tr('Input faults'), [ParameterVector.VECTOR_TYPE_LINE], True))

        self.addParameter(ParameterNumber(self.STEP_X_VALUE, self.tr('Step X'), 0, None, 0, True))
        self.addParameter(ParameterNumber(self.STEP_Y_VALUE, self.tr('Step Y'), 0, None, 0, True))

        self.addParameter(ParameterNumber(self.EXPAND_PERCENT_X, self.tr('Expand X (%)'), 0, None, 10, True))
        self.addParameter(ParameterNumber(self.EXPAND_PERCENT_Y, self.tr('Expand Y (%)'), 0, None, 10, True))

        # We add a raster layer as output
        self.addOutput(OutputRaster(self.OUTPUT_LAYER, self.tr('Output surface')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        output = self.getOutputValue(self.OUTPUT_LAYER)

        self.plugin_dir = os.path.dirname(__file__)
#        self.temp_path = tempfile.gettempdir()
        self.tempPointsFilename = getTempFilename('txt').replace("\\","/")
        #self.temp_path.replace("\\","/") + '/temppoints.txt'
        self.tclFilename = getTempFilename('tcl')
        #os.path.join(self.temp_path, 'tempjob.tcl')
        self.faultFilename = None

        outputFilename, ext = os.path.splitext(output)
        self.grdFilename = getTempFilename('grd').replace("\\","/")
        #self.temp_path.replace("\\","/") + '/tempgrid.grd'

        if inputFilename is None:
            return

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        vectorLayer = dataobjects.getObjectFromUri(inputFilename)
        self.extent = vectorLayer.extent()
        provider = vectorLayer.dataProvider()

        self.stepX = self.getParameterValue(self.STEP_X_VALUE)
        self.stepY = self.getParameterValue(self.STEP_Y_VALUE)
        if self.stepX < 1:
            self.stepX = self.extent.width() / 100
        if self.stepY < 1:
            self.stepY = self.extent.height() / 100

        self.prepareInputData()
        self.prepareJob()
        self.runSurfit(progress)

        runStr = 'gdal_translate -a_nodata -999 -a_srs "{0}" "{1}" "{2}"'.format(provider.crs().toProj4(), self.grdFilename, output )
        self.runProcess(runStr, progress)


    def prepareInputData(self):
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        inputFaultFilename = self.getParameterValue(self.INPUT_FAULT)
        input_field = self.getParameterValue(self.INPUT_FIELD)

        vectorLayer = dataobjects.getObjectFromUri(inputFilename)

        features = vectorLayer.getFeatures()
        with open(self.tempPointsFilename, "w") as text_file:
            for f in features:
                pt = f.geometry().asPoint()
                val = f.attribute(input_field)
                text_file.write("{0} {1} {2}\n".format(pt.x(), pt.y(), val))

        if inputFaultFilename is None:
            return

        #Create fault lines SHP
        vectorLayer = dataobjects.getObjectFromUri(inputFaultFilename)
        provider = vectorLayer.dataProvider()

        self.faultFilename = getTempFilename('shp').replace("\\", "/")
        #self.temp_path.replace("\\", "/") + '/tempfaults.shp'
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields = [QgsField('NAME', QVariant.String)]
        writer = VectorWriter(self.faultFilename, systemEncoding,
                              fields,
                              provider.geometryType(), provider.crs())

        features = provider.getFeatures(QgsFeatureRequest(self.extent))
        num = 1
        for f in features:
            l = f.geometry()
            feat = QgsFeature()
            feat.setGeometry(l)
            feat.setAttributes(['fault{0}'.format(num)])
            num = num + 1
            writer.addFeature(feat)
        del writer


    def prepareJob(self):
        with open(self.tclFilename, "w") as text_file:
            # load plugins
            text_file.write("load libsurfit[info sharedlibextension]\n")
            text_file.write("load libsurfit_io[info sharedlibextension]\n")
            # remove all previous data and gridding rules
            text_file.write("clear_data\n")
            # set name of surface
            text_file.write('set map_name "map_faults"\n')
            # set solver
            text_file.write('set_solver "cg"\n')
            # set tolerance for solver
            text_file.write('set tol 1e-005\n')
            ##
            ## load initial data
            ##
            # load points from text file
            text_file.write('pnts_read "{0}" "points1"\n'.format(self.tempPointsFilename))

            if self.faultFilename:
                # load faults from Surfer BLN file
                text_file.write('curv_load_shp "{0}"\n'.format(self.faultFilename))

            ##
            ## construct grid
            ##

            expX = self.getParameterValue(self.EXPAND_PERCENT_X)
            expY = self.getParameterValue(self.EXPAND_PERCENT_Y)
            deltaX = self.extent.width() / 100.0 * expX
            deltaY = self.extent.height() / 100.0 * expY
            text_file.write("grid_get {0} {1} {2} {3} {4} {5}\n".format(self.extent.xMinimum()-deltaX/2,
                                                                self.extent.xMaximum()+deltaX/2,
                                                                self.stepX,
                                                                self.extent.yMinimum()-deltaY/2,
                                                                self.extent.yMaximum()+deltaY/2,
                                                                self.stepY))
            # text_file.write("grid 50 50\n")
            ##
            ## create gridding rules
            ##
            # resulting surface at points = points values
            text_file.write('points "points1"\n')

            if self.faultFilename:
                text_file.write('fault "fault*"\n')

            # resulting surface should tend to be constant or plane
            text_file.write("completer 1 5 \n")
            ##
            ## run gridding algorithm
            ##
            text_file.write("surfit \n")
            ##
            ## save results
            ##
            # save surface to Surfer-ASCII grid file
            text_file.write('surf_save_grd "{0}" $map_name \n'.format(self.grdFilename))


    def runSurfit(self, progress):
        runStr = os.path.join(self.plugin_dir, "bin/surfit ") + os.path.realpath(self.tclFilename)
        self.runProcess(runStr, progress)

    def runProcess(self, runStr, progress):
        process = QProcess(iface)
        process.start(runStr)
        process.waitForFinished()
        returnedstring = str(process.readAllStandardOutput())
        # print returnedstring
        progress.setInfo(returnedstring)
        process.kill()

