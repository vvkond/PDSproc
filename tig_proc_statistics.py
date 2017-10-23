# -*- coding: utf-8 -*-

__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os
import shutil

from PyQt4.QtCore import QSettings, QProcess, QVariant
from qgis.analysis import QgsGeometryAnalyzer
from qgis.utils import iface
from qgis.core import *

import processing
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterRange
from processing.core.parameters import ParameterSelection
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterNumber
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputTable
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter


class TigStatisticsAlgorithm(GeoAlgorithm):

    OUTPUT_OBJECT = 'OUTPUT_TABLE'
    INPUT_POINTS = 'INPUT_LAYER1'
    INPUT_FAULT = 'INPUT_FAULT'
    INPUT_FIELD = 'INPUT_FIELD'
    INPUT_MIN_VALUE = 'DATA_MIN_VALUE'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = self.tr(u'Calculate Statistic')

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # Input Control points
        self.addParameter(ParameterVector(self.INPUT_POINTS,
                      self.tr('Control point set'), [ParameterVector.VECTOR_TYPE_POINT]))

        # Input column
        self.addParameter(ParameterTableField(self.INPUT_FIELD, self.tr('Column from set'),
                                              self.INPUT_POINTS, ParameterTableField.DATA_TYPE_NUMBER))

        #Data min value
        self.addParameter(ParameterNumber(self.INPUT_MIN_VALUE, self.tr('Data min value'), 0, None, 0))

        # We add a vector layer as output
        self.addOutput(OutputTable(self.OUTPUT_OBJECT, self.tr('Output table')))

    def getParameterValue(self, paramName):
        print paramName
        return super(TigStatisticsAlgorithm, self).getParameterValue(paramName)

    def processAlgorithm(self, progress):
        pass
