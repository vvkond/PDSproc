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
from osgeo import gdal

import processing
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterNumber
from processing.core.outputs import OutputTable
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter
from processing.tools.system import getTempFilename


class TigReservesByRasterAlgorithm(GeoAlgorithm):
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
    INPUT_POLYGON = 'INPUT_POLYGON'
    INTERVAL = 'INTERVAL'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = self.tr(u'Reserves calculation')
        self.description = self.tr(u"Calculate HC reserves using TopTVD raster and OWC\
                                    polygon imported from corporate database")

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Grids')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterRaster(self.INPUT_LAYER, self.tr('Input TopTVD Raster'), False))
        self.addParameter(ParameterVector(self.INPUT_POLYGON,
                      self.tr('Input OWC polygon'), [ParameterVector.VECTOR_TYPE_POLYGON,
                                                     ParameterVector.VECTOR_TYPE_LINE], False))

        # We add a vector layer as output
        self.addOutput(OutputTable(self.OUTPUT_LAYER, self.tr('Output file')))


    def processAlgorithm(self, progress):
        self.mProgress = progress

        in_tvd = self.getParameterValue(self.INPUT_LAYER)
        in_owc = self.getParameterValue(self.INPUT_POLYGON)
        out_Reserves = self.getOutputValue(self.OUTPUT_LAYER)

        # Initialise temporary variables
        # Polygons creared from lines
        rasterLayer = dataobjects.getObjectFromUri(in_tvd)
        vectorLayer = dataobjects.getObjectFromUri(in_owc)
        geometryType = vectorLayer.geometryType()
        owc_poly_tmp = in_owc
        if geometryType == QGis.Line:
            owc_poly_tmp = getTempFilename('shp')
            processing.runalg("qgis:linestopolygons", in_owc, owc_poly_tmp)

        #Get raster info
        extent = rasterLayer.extent()
        provider = rasterLayer.dataProvider()
        rows = rasterLayer.rasterUnitsPerPixelY()
        cols = rasterLayer.rasterUnitsPerPixelX()
        block = provider.block(1, extent, rows, cols)
        noDataValue = block.noDataValue()
        cellSizeX = rasterLayer.rasterUnitsPerPixelX()
        cellSizeY = rasterLayer.rasterUnitsPerPixelY()
        cellArea = cellSizeX * cellSizeY

        # Clipped raster
#        tvd_clip_r = getTempFilename('tif')#scratch + "\\tvd_clip_r"
        points_v = getTempFilename('shp')#scratch + "\\out_r"
        # statistic = scratch + "\\statistic"

        #Raster to points
        progress.setInfo('Convert raster to point node')
        progress.setInfo(points_v)
        processing.runalg('saga:gridvaluestopoints', {"GRIDS": [in_tvd],
                                                    "POLYGONS": owc_poly_tmp,
#                                                            "NODATA": 'True',
                                                    "TYPE": 0,
                                                    "SHAPES":points_v} )
        pointsLayer = QgsVectorLayer(points_v, 'nodes', 'ogr')

        # Process: Extract by Mask
#        processing.runalg('gdalogr:cliprasterbymasklayer', {"INPUT":in_tvd,
#                                                            "MASK":owc_poly_tmp,
#                                                            "NO_DATA": noDataValue,
#                                                            "OUTPUT":tvd_clip_r} )
#        progress.setInfo("Clipped raster:{}".format(tvd_clip_r))

        try:
            fields = pointsLayer.fields()
            lastField = fields.count()-1
            lastFieldName = fields[lastField].name()
            tvdMAX = pointsLayer.maximumValue(lastField)
            tvdMIN = pointsLayer.minimumValue(lastField)
        except e:
            progress.setInfo(str(e))
            return

        NoIntervals = 5
        thick = int((float(tvdMAX) - float(tvdMIN)) / NoIntervals)

        # Write raster_area to a  file
        # workfile=scratch + "\\raster_area.txt"
        workfile = out_Reserves
        try:
            # Clean the file

            f = open(workfile, 'w')
            f.write("DEPTH;CumArea@F90;F50;F10 \n")
            f.close()

            # simple list
            list1 = []
            # nested list
            outline = []
            self.curVolume = 0
            for i in range(NoIntervals + 1):
                slice = int(float(tvdMIN) / thick + i + 1) * thick

                expr = QgsExpression('\"{0}\">\'{1}\' AND \"{2}\"<=\'{3}\''.format(lastFieldName, slice-thick, lastFieldName, slice))
                searchRes = pointsLayer.getFeatures(QgsFeatureRequest(expr))
                num = 0
                for f in searchRes:
                    num += 1
                list1.append(slice)
                list1.append(num * cellArea)
                outline.append(list1)
                list1 = []
                # Execute SurfaceVolume
#                processing.runalg('saga:gridvolume', tvd_clip_r, 1, slice, progress=self)
#                print slice, self.curVolume
#                volume = arcpy.SurfaceVolume_3d(Raster(tvd_clip_r), "", "BELOW", slice, "", "")
#                line = volume.getMessages(0) + "\n"
                # remove leading and trailing spaces
#                x = line.strip()
                # convert string to list separated by spaces
#                y = x.split(" ")
#                list1.append(y[5])
#                area = y[17]
#                list1.append(area[5:])
#                outline.append(list1)
#                list1 = []

        except Exception as e:
            # If an error occurred print the message to the screen
            progress.setInfo(str(e))

        try:
            f = open(workfile, 'a')
            for i in range(len(outline)):
                if (i == 0):
                    p90 = float(outline[0][1]) * 0.8 / 1000000
                else:
                    p90 = float(outline[i - 1][1]) / 1000000
                if (i == len(outline) - 1):
                    p10 = float(outline[i][1]) * 1.2 / 1000000
                else:
                    p10 = float(outline[i + 1][1]) / 1000000
                output = str(outline[i][0]) + ";" + str(p90) + ";" + str(float(outline[i][1]) / 1000000) + ";" + str(
                    p10) + "\n"
                f.write(output)

            f.close()
        except Exception as e:
            # If an error occurred print the message to the screen
            progress.setInfo(str(e))

    def error(self, msg):
        print "Error", msg

    def setCommand(self, cmd):
        return

    def addMessage(self, fmt, *a, **kw):
        print fmt.format(*a, **kw)

    def setPercentage(self, val):
        return

    def setText(self, text):
        return

    def setInfo(self, text):
        self.mProgress.setInfo(text)

    def setConsoleInfo(self, text):
        if 'Grid Volume: Volume:' in text:
            ss = text.replace('Grid Volume: Volume:', '')
            self.curVolume = float(ss)

    def polylineToPolygon(self, linesLayer, output):
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields = processing.fields(linesLayer)
        writer = VectorWriter(output, systemEncoding, fields, QGis.WKBPolygon, linesLayer.crs())
        feats = processing.features(linesLayer)
        for feat in feats:
            geom = feat.geometry()


