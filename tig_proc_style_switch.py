# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2018-12-03'
__copyright__ = '(C) 2018 by Alex Russkikh'

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
from processing.core.parameters import ParameterTableField,ParameterTableMultipleField,ParameterMultipleInput
from processing.core.parameters import ParameterBoolean,ParameterString
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter

#===============================================================================
# 
#===============================================================================
class TigSwitchLayerStyleAlgorithm(GeoAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    STYLE="PREFIX"
    
    ##_joinfield__to=optional field Layer_to_update
    ##_joinfield__from=optional field Layer_from_update

    #===========================================================================
    # 
    #===========================================================================
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        
        In console try:
            from processing.core import parameters 
            dir(parameters) 
            
        https://gis.stackexchange.com/questions/156800/custom-qgis-processing-tool-fails-to-copy-features
        https://github.com/qgis/QGIS/blob/master/python/plugins/processing/core/parameters.py
        """

        # The name that the user will see in the toolbox
        self.name = self.tr(u'Switch layer style')
        self.i18n_name = u'Переключение стиля слоя'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        
        #---------------LAYER A
#         self.addParameter(
#             ParameterVector(
#                 self.LAYER_TO  #layer id
#                 , self.tr('Layer to update') #display text
#                 , [ParameterVector.VECTOR_TYPE_POINT,ParameterVector.VECTOR_TYPE_LINE] #layer types
#                 , False #[is Optional?]
#                 ))

        self.addParameter(
            ParameterVector(
                self.LAYER_TO  #layer id
                , self.tr('Layer to update') #display text
                , ParameterVector.VECTOR_TYPE_ANY #layer types
                , False #[is Optional?]
                ))

        self.addParameter(
            ParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                self.STYLE    #name
                , u'Стиль' #desc
                , 'default' #default
                , False # is big text?
                , True
                #, False #for 2.14
                ))   
         
        
    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        progress.setText('<b>Start</b>')
        
        
        progress.setText('Read settings')
        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        Layer_to_update      = self.getParameterValue(self.LAYER_TO)
        _style               = self.getParameterValue(self.STYLE)
        #--- create virtual field with geometry
        progress.setText('Try change style <b>{}</b> -> <b>{}</b>'.format(Layer_to_update,_style))
        Layer_to_update=dataobjects.getObject(Layer_to_update)      #processing.getObjectFromUri()
        LayerStyles=Layer_to_update.styleManager()
        LayerStyles.setCurrentStyle(_style)
        progress.setText('<b>End</b>')
            
                    
        