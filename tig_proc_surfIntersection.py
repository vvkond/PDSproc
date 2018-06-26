# -*- coding: utf-8 -*-


__author__ = 'Viktor Kondrashov'
__date__ = '2018-06-08'
__copyright__ = '(C) 2018 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from PyQt4.QtCore import QSettings, QProcess, QVariant
from qgis.utils import iface
from qgis.core import *
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator

import processing
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField, ParameterBoolean
from processing.core.outputs import OutputRaster, OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter
from processing.tools.system import getTempFilename

class TigSurfaceIntersectCorrectAlgorithm(GeoAlgorithm):
    OUTPUT_SURFACE = 'OUTPUT_RASTER'
    TOP_SURFACE = 'TOP_SURFACE'
    BOTTOM_SURFACE = 'BOTTOM_SURFACE'

    def defineCharacteristics(self):
        self.name = self.tr(u'Surface intersection')

        # The branch of the toolbox under which the algorithm will appear
        self.group = u'Grids'

        self.addParameter(ParameterRaster(self.TOP_SURFACE,
                                          self.tr('Top surface'), False))
        self.addParameter(ParameterRaster(self.BOTTOM_SURFACE,
                                          self.tr('Bottom surface'), False))

        self.addOutput(OutputRaster(self.OUTPUT_SURFACE, self.tr('Output surface')))


    def processAlgorithm(self, progress):
        output = self.getOutputValue(self.OUTPUT_SURFACE)
        topSurfaceName = self.getParameterValue(self.TOP_SURFACE)
        bottomSurfaceName = self.getParameterValue(self.BOTTOM_SURFACE)


        bottomRaster = dataobjects.getObjectFromUri(bottomSurfaceName)
        topRaster = dataobjects.getObjectFromUri(topSurfaceName)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = topRaster
        ras.bandNumber = 1
        entries.append(ras)
        ras1 = QgsRasterCalculatorEntry()
        ras1.ref = 'ras1@1'
        ras1.raster = bottomRaster
        ras1.bandNumber = 1
        entries.append(ras1)
        calc = QgsRasterCalculator('ras@1 + (ras1@1 - ras@1) * ((ras1@1 - ras@1) >= 0)', output, 'GTiff', bottomRaster.extent(),
                                   bottomRaster.width(), bottomRaster.height(), entries)
        calc.processCalculation()

