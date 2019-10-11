# -*- coding: utf-8 -*-

__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import glob, os
import shutil

from PyQt4.QtCore import QSettings, QProcess, QVariant
from qgis.analysis import QgsGeometryAnalyzer
from qgis.utils import iface
from qgis.core import *

import processing
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterNumber
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter
from processing.tools.system import getTempFilename


class TigContouringAlgorithm(GeoAlgorithm):
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
    INPUT_LAYER = 'INPUT_LAYER1'
    INPUT_FAULT = 'INPUT_FAULT'
    INTERVAL = 'INTERVAL'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = u'Create isolines'
        self.i18n_name = u'Снятие изолиний'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Grids')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterRaster(self.INPUT_LAYER, self.tr('Input layer'), False))
        self.addParameter(ParameterVector(self.INPUT_FAULT,
                      self.tr('Input faults'), [ParameterVector.VECTOR_TYPE_LINE], True))
        self.addParameter(ParameterNumber(self.INTERVAL, self.tr('Interval'), 0, None, 10, True))

        # We add a vector layer as output
        self.addOutput(OutputVector(self.OUTPUT_LAYER, self.tr('Output layer')))


    def processAlgorithm(self, progress):
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        output = self.getOutputValue(self.OUTPUT_LAYER)
        inputFaultFilename = self.getParameterValue(self.INPUT_FAULT)
        self.Inter = self.getParameterValue(self.INTERVAL)

        rasterLayer = dataobjects.getObjectFromUri(inputFilename)
        self.extent = rasterLayer.extent()

        self.plugin_dir = os.path.dirname(__file__)
        self.temp_path = tempfile.gettempdir()

        if inputFaultFilename is not None:
            self.contourWithFaults(rasterLayer, inputFaultFilename, output, progress )
        else:
            processing.runalg('gdalogr:contour', inputFilename, self.Inter, 'ELEV', None, output)

        self.grdFilename = getTempFilename('grd').replace("\\", "/")
        #self.temp_path.replace("\\", "/") + '/tempgrid.grd'
        self.outputFilename = output.replace("\\", "/")
        self.tclFilename = os.path.join(self.temp_path, 'tempjob.tcl')


    def contourWithFaults(self, rasterLayer, inputFaultFilename, output, progress):
        # bufferLayerName = os.tempnam()+'_buf_layer.shp'
        bufferLayerName = getTempFilename('shp')
        cellSize = min(self.extent.width() / rasterLayer.width(), self.extent.height() / rasterLayer.height())
        provider = rasterLayer.dataProvider()
        rows = rasterLayer.rasterUnitsPerPixelY()
        cols = rasterLayer.rasterUnitsPerPixelX()
        block = provider.block(1, self.extent, rows, cols)
        noDataValue = block.noDataValue()

        faultLayer = dataobjects.getObjectFromUri(inputFaultFilename)
        if faultLayer is None:
            return

        #Create lines buffer
        QgsGeometryAnalyzer().buffer(faultLayer, bufferLayerName, cellSize, False, False, -1, None)

        bufferLayer = processing.getObject(bufferLayerName)
        provider = bufferLayer.dataProvider()
        provider.addAttributes([QgsField('faultParam', QVariant.Double)])
        bufferLayer.updateFields()

        with edit(bufferLayer):
            new_field_index = bufferLayer.fieldNameIndex('faultParam')
            for f in processing.features(bufferLayer):
                bufferLayer.changeAttributeValue(f.id(), new_field_index, noDataValue)

        fn,ext = os.path.splitext(rasterLayer.source())
        ext = ext.replace('.', '')
        tempRasterName = getTempFilename(ext) #os.tempnam() + '_temp_raster_' + ext
        shutil.copyfile(rasterLayer.source(), tempRasterName)
        processing.runalg('gdalogr:rasterize_over', bufferLayerName, 'faultParam', tempRasterName)
        processing.runalg('gdalogr:contour', tempRasterName, self.Inter, 'ELEV', None, output)
        # try:
        #     toRemoveTmpl = self.temp_path + '/*_buf_layer.*'
        #     self.purge(toRemoveTmpl)
        # except Exception as e:
        #     progress.setInfo(str(e))
        #
        # try:
        #     toRemoveTmpl = self.temp_path + '/*_temp_raster_.*'
        #     self.purge(toRemoveTmpl)
        # except Exception as e:
        #     progress.setInfo(str(e))


    def prepareInputData(self):
        inputFaultFilename = self.getParameterValue(self.INPUT_FAULT)
        self.faultFilename = None

        if inputFaultFilename is None:
            return

        #Create fault lines SHP
        self.faultFilename = self.temp_path.replace("\\", "/") + '/tempfaults.shp'
        vectorLayer = dataobjects.getObjectFromUri(inputFaultFilename)

        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        provider = vectorLayer.dataProvider()
        fields = [QgsField('NAME', QVariant.String)]
        writer = VectorWriter(self.faultFilename, systemEncoding,
                                     fields,
                                     provider.geometryType(), provider.crs())

        features = vectorLayer.getFeatures(QgsFeatureRequest(self.extent))
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
            text_file.write('surf_load_grd "{0}" "mysurf"\n'.format(self.grdFilename))

            if self.faultFilename:
                # load faults from Surfer BLN file
                text_file.write('curv_load_shp "{0}"\n'.format(self.faultFilename))

            if self.faultFilename:
                text_file.write('fault "fault*"\n')

            # resulting surface should tend to be constant or plane
            text_file.write('surf_trace_cntr "mysurf"\n')
            ##
            ## save results
            ##
            # save surface to Surfer-ASCII grid file
            text_file.write('cntr_save_shp "{0}" "mysurf*"\n'.format(self.outputFilename))


    def runSurfit(self):
        runStr = os.path.join(self.plugin_dir, "bin/surfit ") + os.path.realpath(self.tclFilename)
        process = QProcess(iface)
        process.start(runStr)
        process.waitForFinished()
        # returnedstring = str(process.readAllStandardOutput())
        # print returnedstring
        # progress.setText(returnedstring)
        process.kill()

    def purge(self, pattern):
        for f in glob.glob(pattern):
            print f
            os.remove(f)
