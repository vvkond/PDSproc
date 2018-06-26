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
from processing.core.parameters import ParameterRaster, ParameterNumber
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField, ParameterBoolean
from processing.core.outputs import OutputRaster, OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter
from processing.tools.system import getTempFilename

class TigVolumeMethodAlgorithm(GeoAlgorithm):
    OUTPUT_SURFACE = 'OUTPUT_RASTER'
    TOP_SURFACE = 'TOP_SURFACE'
    BOTTOM_SURFACE = 'BOTTOM_SURFACE'
    PORO_SURFACE = 'POROSITY_SURFACE'
    NTG_SURFACE = 'NTG_SURFACE'
    VNK_VALUE = 'VNK'

    def defineCharacteristics(self):
        self.name = self.tr(u'Volume method')
        self.description = u'Подсчет запасов объемным методом'

        # The branch of the toolbox under which the algorithm will appear
        self.group = u'Grids'

        self.addParameter(ParameterRaster(self.TOP_SURFACE,
                                          u'Поверхность кровли', False))
        self.addParameter(ParameterRaster(self.BOTTOM_SURFACE,
                                          u'Поверхность подошвы', False))
        self.addParameter(ParameterRaster(self.NTG_SURFACE,
                                          u'Поверхность песчанистости', False))
        self.addParameter(ParameterRaster(self.PORO_SURFACE,
                                          u'Поверхность пористости', False))
        self.addParameter(ParameterNumber(self.VNK_VALUE, u'Уровень ВНК ', 0, None, 2500, False))

        self.addOutput(OutputRaster(self.OUTPUT_SURFACE, self.tr('Output surface')))


    def processAlgorithm(self, progress):
        output = self.getOutputValue(self.OUTPUT_SURFACE)
        topSurfaceName = self.getParameterValue(self.TOP_SURFACE)
        bottomSurfaceName = self.getParameterValue(self.BOTTOM_SURFACE)
        ntgSurfaceName = self.getParameterValue(self.NTG_SURFACE)
        poroSurfaceName = self.getParameterValue(self.PORO_SURFACE)
        vnkValue = self.getParameterValue(self.VNK_VALUE)


        bottomRaster = dataobjects.getObjectFromUri(bottomSurfaceName)
        topRaster = dataobjects.getObjectFromUri(topSurfaceName)
        ntgRaster = dataobjects.getObjectFromUri(ntgSurfaceName)
        poroRaster = dataobjects.getObjectFromUri(poroSurfaceName)
        
        formula = '( base@1 - top@1 ) * ( base@1 <= {0} ) + ( {0} - top@1 ) * ( base@1 > {0} ) * ' \
                  '( (  base@1 - top@1 ) * ( base@1 <= {0}) + ( {0} - top@1 ) * ( base@1 > {0} ) > 0)'.format(vnkValue)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'top@1'
        ras.raster = topRaster
        ras.bandNumber = 1
        entries.append(ras)
        ras1 = QgsRasterCalculatorEntry()
        ras1.ref = 'base@1'
        ras1.raster = bottomRaster
        ras1.bandNumber = 1
        entries.append(ras1)
        calc = QgsRasterCalculator(formula, output, 'GTiff', bottomRaster.extent(),
                                   bottomRaster.width(), bottomRaster.height(), entries)
        calc.processCalculation()


