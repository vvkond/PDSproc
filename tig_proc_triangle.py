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

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter


class TigTriangleAlgorithm(GeoAlgorithm):
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

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = u'Triangulate'
        self.i18n_name = u'Триангуляция'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Vectors')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterVector(self.INPUT_LAYER,
                                          self.tr('Input points'), [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterTableField(self.INPUT_FIELD, self.tr('Field name'),
                                              self.INPUT_LAYER, ParameterTableField.DATA_TYPE_NUMBER))

        self.addParameter(ParameterVector(self.INPUT_FAULT,
                                          self.tr('Input faults'), [ParameterVector.VECTOR_TYPE_LINE], True))

        # We add a vector layer as output
        self.addOutput(OutputVector(self.OUTPUT_LAYER, self.tr('Output layer')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        inputFilename = self.getParameterValue(self.INPUT_LAYER)

        self.plugin_dir = os.path.dirname(__file__)
        self.temp_path = tempfile.gettempdir()
        self.tempPointsFilename = self.temp_path.replace("\\", "/") + '/temppoints.poly'
        self.tempEleFilename = self.temp_path.replace("\\", "/") + '/temppoints.1.ele'
        self.tempNodeFilename = self.temp_path.replace("\\", "/") + '/temppoints.1.node'
        self.faultFilename = None

        if inputFilename is None:
            return

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        self.vectorLayer = dataobjects.getObjectFromUri(inputFilename)
        self.extent = self.vectorLayer.extent()
        provider = self.vectorLayer.dataProvider()

        self.options = "-c"
        self.prepareInputData()
        self.runTriangle()
        self.readResults()


    def prepareInputData(self):
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        inputFaultFilename = self.getParameterValue(self.INPUT_FAULT)
        input_field = self.getParameterValue(self.INPUT_FIELD)

        vectorLayer = dataobjects.getObjectFromUri(inputFilename)
        numPoints = vectorLayer.featureCount()
        if inputFaultFilename is not None:
            self.options = "-c -p -q"
            faultLayer = dataobjects.getObjectFromUri(inputFaultFilename)
            features = faultLayer.getFeatures(QgsFeatureRequest(self.extent))
            for f in features:
                pline = f.geometry().asPolyline()
                numPoints = numPoints + len(pline)

        with open(self.tempPointsFilename, "w") as text_file:
            features = vectorLayer.getFeatures()
            text_file.write("{0} 2 1 0\n".format(numPoints))
            num = 1
            for f in features:
                pt = f.geometry().asPoint()
                val = f.attribute(input_field)
                text_file.write("{0} {1} {2} {3}\n".format(num, pt.x(), pt.y(), val))
                num = num + 1

            #
            # #Add fault lines SHP
            #
            if inputFaultFilename is None:
                text_file.write("0 0\n0\n")
                return

            startNum = num
            features = faultLayer.getFeatures(QgsFeatureRequest(self.extent))
            for f in features:
                pline = f.geometry().asPolyline()
                for pt in pline:
                    text_file.write("{0} {1} {2} 0\n".format(num, pt.x(), pt.y()))
                    num = num + 1

            text_file.write("{0} 0\n".format(faultLayer.featureCount()))
            features = faultLayer.getFeatures(QgsFeatureRequest(self.extent))
            for f in features:
                pline = f.geometry().asPolyline()
                for num in range(1,len(pline)):
                    text_file.write("{0} {1} {2}\n".format(num, startNum, startNum+1))
                    startNum = startNum + 1
            text_file.write("0\n0\n")



    def runTriangle(self):
        runStr = os.path.join(self.plugin_dir, "bin/triangle {0} ".format(self.options)) + os.path.realpath(self.tempPointsFilename)
        process = QProcess(iface)
        process.start(runStr)
        process.waitForFinished()
        # returnedstring = str(process.readAllStandardOutput())
        # print returnedstring
        process.kill()

    def readResults(self):
        output = self.getOutputValue(self.OUTPUT_LAYER)
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields = [QgsField('value', QVariant.Double)]
        writer = VectorWriter(output, systemEncoding, fields, QGis.WKBPolygon, self.vectorLayer.crs())

        nodes = []
        with open(self.tempNodeFilename, "r") as text_file:
            head = text_file.readline()
            count = int(head.split()[0])
            for i in xrange(count):
                line = text_file.readline()
                strVals = line.split()
                coords = [float(strVals[1]), float(strVals[2]), float(strVals[3])]
                nodes.append(coords)

        if len(nodes) < 3:
            return

        with open(self.tempEleFilename, "r") as text_file:
            head = text_file.readline()
            count = int(head.split()[0])
            for i in xrange(count):
                line = text_file.readline()
                strVals = line.split()
                numbers = [int(strVals[1]), int(strVals[2]), int(strVals[3])]
                coord1 = nodes[numbers[0]-1]
                coord2 = nodes[numbers[1]-1]
                coord3 = nodes[numbers[2]-1]
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolygon([[QgsPoint(coord1[0], coord1[1]),
                                                           QgsPoint(coord2[0], coord2[1]),
                                                           QgsPoint(coord3[0], coord3[1])]]))
                feat.setAttributes([coord1[2]])
                writer.addFeature(feat)

        del writer
