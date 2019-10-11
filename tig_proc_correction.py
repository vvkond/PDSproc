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

class TigSurfaceCorrectionAlgorithm(GeoAlgorithm):
    OUTPUT_LAYER = 'OUTPUT_LAYER'
    OUTPUT_QVECTOR = 'OUTPUT_QVECTOR'
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FAULT = 'INPUT_FAULT'
    INPUT_FIELD = 'INPUT_FIELD'
    INPUT_RASTER = 'INPUT_RASTER'

    def defineCharacteristics(self):
        self.name = u'Surface correction'
        self.i18n_name = u'Корректировка поверхности'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Grids')

        self.addParameter(ParameterRaster(self.INPUT_RASTER,
                                          u'Поверхность для корректировки', False))

        self.addParameter(ParameterVector(self.INPUT_LAYER,
                                          u'Точки для корректировки поверхности', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterTableField(self.INPUT_FIELD, u'Поле',
                                              self.INPUT_LAYER, ParameterTableField.DATA_TYPE_NUMBER))

        self.addParameter(ParameterVector(self.INPUT_FAULT,
                                          u'Разломы', [ParameterVector.VECTOR_TYPE_LINE], True))

        self.addOutput(OutputRaster(self.OUTPUT_LAYER, u'Откорректированная поверхность'))
        self.addOutput(OutputVector(self.OUTPUT_QVECTOR, u'Контроль качества корректировки'))

    def processAlgorithm(self, progress):
        inputSurfaceName = self.getParameterValue(self.INPUT_RASTER)
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        output = self.getOutputValue(self.OUTPUT_LAYER)
        outputVector = self.getOutputValue(self.OUTPUT_QVECTOR)
        inputFaultFilename = self.getParameterValue(self.INPUT_FAULT)
        inputField = self.getParameterValue(self.INPUT_FIELD)

        rasterLayer = dataobjects.getObjectFromUri(inputSurfaceName)
        self.extent = rasterLayer.extent()

        pointsLayer = dataobjects.getObjectFromUri(inputFilename)
        pointsProvider = pointsLayer.dataProvider()

        tempResidualName = getTempFilename('shp')
        progress.setInfo(tempResidualName)
        tempDeltasName = getTempFilename('tif')
        progress.setInfo(tempDeltasName)

        fields = pointsProvider.fields().toList()
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields.append(('Delta1', QVariant.Double))
        writer = VectorWriter(tempResidualName, systemEncoding,
                              fields,
                              QGis.WKBPoint, pointsProvider.crs())

        #1. Extract surface points and write deltas
        progress.setInfo('Step 1: Extraxt surface points and write deltas')
        features = pointsProvider.getFeatures()
        for f in features:
            pointGeom = f.geometry()
            if pointGeom.wkbType() == QGis.WKBMultiPoint:
                pointPoint = pointGeom.asMultiPoint()[0]
            else:
                pointPoint = pointGeom.asPoint()

            attrs = f.attributes()
            inputAttr = float(f.attribute(inputField))

            outFeat = QgsFeature()
            outFeat.setGeometry(pointGeom)

            rastSample = rasterLayer.dataProvider().identify(pointPoint, QgsRaster.IdentifyFormatValue).results()
            if rastSample and len(rastSample):
                attrs.append(inputAttr - float(rastSample[rastSample.keys()[0]]))
            else:
                attrs.append(None)

            outFeat.initAttributes(1)
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)
        del writer
        writer = None
        progress.setPercentage(25)


        #2.Make delta`s surface
        progress.setInfo('Step 2: Make delta`s surface')
        strExtent = '{0},{1},{2},{3}'.format(self.extent.xMinimum(), self.extent.xMaximum(),
                                             self.extent.yMinimum(), self.extent.yMaximum())
        processing.runalg('tigressprocessing:creategridwithfaults', {"INPUT_LAYER": tempResidualName,
                                                                     "INPUT_FIELD": 'Delta1',
                                                                     "INPUT_FAULT" : inputFaultFilename,
                                                                     "INPUT_EXTENT": strExtent,
                                                                     "EXPAND_PERCENT_X" : '0',
                                                                     "EXPAND_PERCENT_Y": '0',
                                                                     "STEP_X": rasterLayer.rasterUnitsPerPixelX(),
                                                                     "STEP_Y": rasterLayer.rasterUnitsPerPixelY(),
                                                                     "OUTPUT_LAYER" : tempDeltasName})
        progress.setPercentage(50)


        #3. Add input surface and delta`s surface
        progress.setInfo('Step 3: Add input surface and delta`s surface')
        tempDeltasRaster = QgsRasterLayer(tempDeltasName, 'TempDeltasLayer')
        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = rasterLayer
        ras.bandNumber = 1
        entries.append(ras)
        ras1 = QgsRasterCalculatorEntry()
        ras1.ref = 'ras1@1'
        ras1.raster = tempDeltasRaster
        ras1.bandNumber = 1
        entries.append(ras1)
        calc = QgsRasterCalculator('ras@1 + ras1@1', output, 'GTiff', rasterLayer.extent(),
                                   rasterLayer.width(), rasterLayer.height(), entries)
        calc.processCalculation()
        progress.setPercentage(75)

        # 4. Extract points from corrected surface
        progress.setInfo('Step 5: Extract points from corrected surface')
        sumRaster = QgsRasterLayer(output, 'sumSurface')
        deltasLayer = QgsVectorLayer(tempResidualName, "testlayer_shp", "ogr")
        fields = deltasLayer.dataProvider().fields().toList()
        fields.append(('Delta2', QVariant.Double))
        writer = VectorWriter(outputVector, systemEncoding,
                              fields,
                              QGis.WKBPoint, pointsProvider.crs())
        for f in deltasLayer.dataProvider().getFeatures():
            pointGeom = f.geometry()
            pointPoint = pointGeom.asPoint()

            attrs = f.attributes()
            inputAttr = float(f.attribute(inputField))

            outFeat = QgsFeature()
            outFeat.setGeometry(pointGeom)

            rastSample = sumRaster.dataProvider().identify(pointPoint, QgsRaster.IdentifyFormatValue).results()
            if rastSample and len(rastSample):
                attrs.append(inputAttr - float(rastSample[rastSample.keys()[0]]))
            else:
                attrs.append(None)

            outFeat.initAttributes(1)
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)
        del writer
        writer = None
        del sumRaster
        sumRaster = None

        progress.setPercentage(100)



