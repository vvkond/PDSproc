# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2019-02-12'
__copyright__ = '(C) 2018 by Alex Russkikh'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from PyQt4.QtCore import QSettings, QProcess, QVariant
from qgis.utils import iface
from qgis.core import *

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput, ParameterNumber,\
    ParameterRange
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter




#===============================================================================
# 
#===============================================================================
class TigShowRuleLabelContours(GeoAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    VALUE_FIELD="VALUE_FIELD"
    LIMITS="LIMITS"
    STEP="STEP"
    SKEEP_EACH="SKEEP_EACH"
    
    PARAMS=[
        [STEP ,"Step for show contours"           ,True ,25    ]
        ,[SKEEP_EACH ,"Skeep each 'n' contours"   ,True  ,0    ]
        ]
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
        self.name = self.tr(u'Show contours with step')
        self.i18n_name = u'Отображение контуров с указанным шагом'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        
        #---------------LAYER A
        self.addParameter(
            ParameterVector(
                self.LAYER_TO  #layer id
                , self.tr('Layer with contours') #display text
                , [ParameterVector.VECTOR_TYPE_LINE] #layer types
                , False #[is Optional?]
                ))

        self.addParameter(
            ParameterTableField(
                self.VALUE_FIELD
                , self.tr('Field {} with contour value ').format(self.VALUE_FIELD) #display text
                , self.LAYER_TO #field layer
                , ParameterTableField.DATA_TYPE_NUMBER
                , False #[is Optional?]
                ))
        self.addParameter(
            ParameterRange( 
                name=self.LIMITS
                , description=self.tr('Interval limits') #display text
                , default='-20000,20000'
                , optional=True
                )
            )
        
        for [param_id,desc,is_optional,param_default] in self.PARAMS:
            self.addParameter(
                ParameterNumber( 
                    name=param_id 
                    , description= desc
                    , minValue=None, maxValue=None
                    , default=param_default
                    , optional=is_optional
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
        Layer_to_update     = self.getParameterValue(self.LAYER_TO)
        _value_field_= self.getParameterValue(self.VALUE_FIELD)
        _range_field_= self.getParameterValue(self.LIMITS)
        _step_field_= self.getParameterValue(self.STEP)
        _skeep_field_= self.getParameterValue(self.SKEEP_EACH)
        

        #--- create virtual field with geometry
        editLayer=dataobjects.getObject(Layer_to_update)      #processing.getObjectFromUri()
        layerCurrentStyleRendere=editLayer.rendererV2()
        if not type(layerCurrentStyleRendere)==QgsRuleBasedRendererV2:
            editLayerStyles=editLayer.styleManager()
            editLayerStyles.addStyle( u'контуры', editLayerStyles.style(editLayerStyles.currentStyle() ))
            editLayerStyles.setCurrentStyle(u'контуры')

            progress.setText('Change style rendered to rule based')
            renderer = QgsRuleBasedRendererV2(QgsRuleBasedRendererV2.Rule(None))
            superRootRule = renderer.rootRule() #super Root Rule
            editLayer.setRendererV2(renderer)
        else:
            superRootRule=layerCurrentStyleRendere.rootRule() 
        #---------
        progress.setText('Create rule')
        symbol = QgsLineSymbolV2.createSimple({ 
                                                    'name' :'0'
                                                 ,  'type': 'line'
                                                 #,  'class':'SimpleLine'
                                                 ,  'alpha':"1"
                                                 ,  'clip_to_extent':"1"
                                                })
        """
           <symbol alpha="1" clip_to_extent="1" type="line" name="0">
            <layer pass="0" class="SimpleLine" locked="0">
             <prop k="capstyle" v="square"/>
             <prop k="customdash" v="5;2"/>
             <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
             <prop k="customdash_unit" v="MM"/>
             <prop k="draw_inside_polygon" v="0"/>
             <prop k="joinstyle" v="bevel"/>
             <prop k="line_color" v="34,139,34,255"/>
             <prop k="line_style" v="solid"/>
             <prop k="line_width" v="0.25"/>
             <prop k="line_width_unit" v="MM"/>
             <prop k="offset" v="0"/>
             <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
             <prop k="offset_unit" v="MM"/>
             <prop k="use_custom_dash" v="0"/>
             <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
            </layer>
           </symbol>
        """        
        sub_rule = QgsRuleBasedRendererV2.Rule(symbol)
        progress.setText('Set rule label')
        sub_rule.setLabel(u'Контуры от {} до {} с шагом {} {}'.format(_range_field_.split(",")[0]
                                                                                      ,_range_field_.split(",")[1]
                                                                                      ,_step_field_
                                                                                      ,u'исключая каждый {}'.format(_skeep_field_) if _skeep_field_>0  else ''
                                                                                      ))
        progress.setText('Set rule filter')
        sub_rule.setFilterExpression(u'isValueInIntervalWithSkeep({value}, {limit_min}, {limit_max}, {step}, {skeep_each})'.format(
            value=_value_field_
            ,limit_min=_range_field_.split(",")[0]
            ,limit_max=_range_field_.split(",")[1]
            ,step=_step_field_
            ,skeep_each=_skeep_field_
            )) 
        superRootRule.appendChild(sub_rule)
        progress.setText('End')
        pass
        
                    
                    
                    
                    
        