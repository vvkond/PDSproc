# -*- coding: utf-8 -*-

import processing

class ProcessingProxy:
    def __init__(self):
        pass

    def rasterize(self, bufferLayerName, fparamName, tempRasterName):
        processing.runalg('gdalogr:rasterize_over', bufferLayerName, fparamName, tempRasterName)