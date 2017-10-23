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


class TigMergeLayersAlgorithm(GeoAlgorithm):
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
    INPUT_LAYER1 = 'INPUT_LAYER1'
    INPUT_LAYER2 = 'INPUT_LAYER2'
    INPUT_FIELD1 = 'INPUT_FIELD1'
    INPUT_FIELD2 = 'INPUT_FIELD2'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = self.tr(u'Merge layers')

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterVector(self.INPUT_LAYER1,
            self.tr('Input layer 1'), [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterTableField(self.INPUT_FIELD1, self.tr('Field name 1'),
            self.INPUT_LAYER1, ParameterTableField.DATA_TYPE_NUMBER))

        self.addParameter(ParameterVector(self.INPUT_LAYER2,
            self.tr('Input layer 2'), [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterTableField(self.INPUT_FIELD2, self.tr('Field name 2'),
                                              self.INPUT_LAYER2, ParameterTableField.DATA_TYPE_NUMBER))

        # We add a vector layer as output
        self.addOutput(OutputVector(self.OUTPUT_LAYER, self.tr('Output layer')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename1 = self.getParameterValue(self.INPUT_LAYER1)
        inputFilename2 = self.getParameterValue(self.INPUT_LAYER2)
        inputField1 = self.getParameterValue(self.INPUT_FIELD1)
        inputField2 = self.getParameterValue(self.INPUT_FIELD2)
        output = self.getOutputValue(self.OUTPUT_LAYER)


        if inputFilename1 is None:
            return

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        vectorLayer1 = dataobjects.getObjectFromUri(inputFilename1)
        vectorLayer2 = dataobjects.getObjectFromUri(inputFilename2)

        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields = [QgsField('value', QVariant.Double)]
        writer = VectorWriter(output, systemEncoding, fields, QGis.WKBPoint, vectorLayer1.crs())

        self.copyLayer(vectorLayer1, inputField1,  writer)
        self.copyLayer(vectorLayer2, inputField2, writer)

        del writer


    def copyLayer(self, inputLayer, inputField, writer):
        geometryType = inputLayer.geometryType()
        iter1 = inputLayer.getFeatures()
        if geometryType == QGis.Point:
            for feature1 in iter1:
                p1 = feature1.geometry().asPoint()
                val = feature1.attribute(inputField)

                l = QgsGeometry.fromPoint(p1)
                feat = QgsFeature()
                feat.setGeometry(l)
                feat.setAttributes([val])
                writer.addFeature(feat)
        elif geometryType == QGis.Line:
            for feature1 in iter1:
                pline = feature1.geometry().asPolyline()
                val = feature1.attribute(inputField)
                for p1 in pline:
                    l = QgsGeometry.fromPoint(p1)
                    feat = QgsFeature()
                    feat.setGeometry(l)
                    feat.setAttributes([val])
                    writer.addFeature(feat)