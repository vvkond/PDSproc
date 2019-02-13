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
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter




#===============================================================================
# 
#===============================================================================
class TigCreateMultilineRuleLabelAlgorithm(GeoAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    FIELD_1="FIELD_1"
    FIELD_2="FIELD_2"
    FIELD_3="FIELD_3"
    FIELD_4="FIELD_4"
    FIELD_5="FIELD_5"
    FIELD_6="FIELD_6"

    #---QGIS 2.18 version. FOr QGIS 3 see QgsRuleBasedLabeling
    TMPL_RULES="""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.28" simplifyAlgorithm="0" minimumScale="0" maximumScale="1e+08" simplifyDrawingHints="0" minLabelScale="0" maxLabelScale="1e+08" simplifyDrawingTol="1" readOnly="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" scaleBasedLabelVisibilityFlag="0">
 <labeling type="rule-based">
  <rules key="{{00000000-1111-2222-3333-{_rnd12_}}}">
  {_rule_}
  </rules>
 </labeling>
</qgis>   
""" #_rule_,_rnd12_
    TMPL_RULE="""   <rule description="{_name_}" filter="{_filter_}" key="{{00000000-1111-2222-3333-{_rnd12_}}}">
    <settings>
     <text-style fontItalic="0" fontFamily="MS Shell Dlg 2" fontLetterSpacing="0" fontUnderline="0" fontWeight="50" fontStrikeout="0" textTransp="0" previewBkgrdColor="#ffffff" fontCapitals="0" textColor="0,0,0,255" fontSizeInMapUnits="0" isExpression="{_is_expression_}" blendMode="0" fontSizeMapUnitScale="0,0,0,0,0,0" fontSize="8.25" fieldName="{_field_}" namedStyle="Normal" fontWordSpacing="0" useSubstitutions="0">
      <substitutions/>
     </text-style>
     <text-format placeDirectionSymbol="0" multilineAlign="3" rightDirectionSymbol=">" multilineHeight="1" plussign="0" addDirectionSymbol="0" leftDirectionSymbol="&lt;" formatNumbers="0" decimals="3" wrapChar="" reverseDirectionSymbol="0"/>
     <text-buffer bufferSize="1" bufferSizeMapUnitScale="0,0,0,0,0,0" bufferColor="255,255,255,255" bufferDraw="1" bufferBlendMode="0" bufferTransp="0" bufferSizeInMapUnits="0" bufferNoFill="0" bufferJoinStyle="128"/>
     <background shapeSizeUnits="1" shapeType="0" shapeSVGFile="" shapeOffsetX="0" shapeOffsetY="0" shapeBlendMode="0" shapeFillColor="255,255,255,255" shapeTransparency="0" shapeSizeMapUnitScale="0,0,0,0,0,0" shapeSizeType="0" shapeJoinStyle="64" shapeDraw="0" shapeBorderWidthUnits="1" shapeSizeX="0" shapeSizeY="0" shapeOffsetMapUnitScale="0,0,0,0,0,0" shapeRadiiX="0" shapeRadiiY="0" shapeOffsetUnits="1" shapeRotation="0" shapeBorderWidth="0" shapeBorderColor="128,128,128,255" shapeRotationType="0" shapeBorderWidthMapUnitScale="0,0,0,0,0,0" shapeRadiiMapUnitScale="0,0,0,0,0,0" shapeRadiiUnits="1"/>
     <shadow shadowOffsetMapUnitScale="0,0,0,0,0,0" shadowOffsetGlobal="1" shadowRadiusUnits="1" shadowTransparency="30" shadowColor="0,0,0,255" shadowUnder="0" shadowScale="100" shadowOffsetDist="1" shadowDraw="0" shadowOffsetAngle="135" shadowRadius="1.5" shadowRadiusMapUnitScale="0,0,0,0,0,0" shadowBlendMode="6" shadowRadiusAlphaOnly="0" shadowOffsetUnits="1"/>
     <placement repeatDistanceUnit="1" placement="1" maxCurvedCharAngleIn="25" repeatDistance="0" distInMapUnits="0" labelOffsetInMapUnits="0" xOffset="0" distMapUnitScale="0,0,0,0,0,0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" preserveRotation="1" repeatDistanceMapUnitScale="0,0,0,0,0,0" centroidWhole="0" priority="5" yOffset="0" offsetType="0" placementFlags="10" centroidInside="0" dist="0" angleOffset="0" maxCurvedCharAngleOut="-25" fitInPolygonOnly="0" quadOffset="2" labelOffsetMapUnitScale="0,0,0,0,0,0"/>
     <rendering fontMinPixelSize="3" scaleMax="10000000" fontMaxPixelSize="10000" scaleMin="1" upsidedownLabels="0" limitNumLabels="0" obstacle="1" obstacleFactor="1" scaleVisibility="0" fontLimitPixelSize="0" mergeLines="0" obstacleType="0" labelPerPart="0" zIndex="0" maxNumLabels="2000" displayAll="1" minFeatureSize="0"/>
     <data-defined>
      <Size expr="" field="lablwidth" active="true" useExpr="false"/>
      <Color expr="" field="lablcol" active="true" useExpr="false"/>
      <Family expr="" field="font" active="true" useExpr="false"/>
      <BufferSize expr="" field="bufwidth" active="true" useExpr="false"/>
      <BufferColor expr="" field="bufcol" active="true" useExpr="false"/>
      <PositionX expr="" field="lablx" active="true" useExpr="false"/>
      <PositionY expr="" field="lably" active="true" useExpr="false"/>
      <BufferDraw expr="&quot;bufcol&quot; is not Null" field="bufcol" active="true" useExpr="true"/>
      <OffsetXY expr="format('%1,%2', &quot;LablOffX&quot; , &quot;LablOffY&quot;)" field="" active="true" useExpr="true"/>
     </data-defined>
    </settings>
   </rule>
"""#_name_, _filter_, _rnd12_, _field_, _is_expression_ 0/1,
    ##_joinfield__to=optional field Layer_to_update
    ##_joinfield__from=optional field Layer_from_update
    #===========================================================================
    # 
    #===========================================================================
    def makeMultilineFormatedLabel(self,label,label_row,row_count):
        """
        <h4>Return</h4>Make formated label for multiline labeled
        <p><h4>Syntax</h4>makeMultilineFormatedLabel(%label%,%row_number%, %row_count%)</p>
        <p><h4>Argument</h4> %row_number%-position start from 0</p>
        <p><h4>Argument</h4> %row_count%-count of rows</p>
        <p><h4>Example</h4>makeMultilineFormatedLabel("well_id",2,10)</p><p>Return: String with inserted new line symbols before and after field value</p>
        """
        #res="\n"*(label_row)+'{}\n'.format(label)+"\n"*(row_count-label_row-1)  
        res="concat("+ "'\\n',"*(label_row)+"{},".format(label)+"'\\n',"*(row_count-label_row-1)
        res=res[:-1]+")" #remove last ','
        return res

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
        self.name = self.tr(u'Create multiline ruled label')
        self.i18n_name = u'Создание многострочной подписи на оснвое правил'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        
        #---------------LAYER A
        self.addParameter(
            ParameterVector(
                self.LAYER_TO  #layer id
                , self.tr('Layer for labeled') #display text
                , [ParameterVector.VECTOR_TYPE_POINT,ParameterVector.VECTOR_TYPE_LINE] #layer types
                , False #[is Optional?]
                ))
        for idx,id in enumerate([self.FIELD_1,self.FIELD_2,self.FIELD_3,self.FIELD_4,self.FIELD_5,self.FIELD_6]):
            self.addParameter(
                ParameterTableField(
                    id
                    , self.tr('Field {} for label ').format(idx) #display text
                    , self.LAYER_TO #field layer
                    , ParameterTableField.DATA_TYPE_ANY
                    , True #[is Optional?]
                    ))
        
    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        progress.setText('<b>Start</b>')
        import random
        from tempfile import NamedTemporaryFile
        
        
        progress.setText('Read settings')
        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        Layer_to_update     = self.getParameterValue(self.LAYER_TO)
        _label_fields_=[ self.getParameterValue(id) for id in [self.FIELD_1,self.FIELD_2,self.FIELD_3,self.FIELD_4,self.FIELD_5,self.FIELD_6]]
        _label_fields_=[x for x in _label_fields_ if x is not None]
        if len(_label_fields_)<1:
            progress.setText('No fields selected.Terminated')
            return

        #--- create virtual field with geometry
        Layer_to_update=dataobjects.getObject(Layer_to_update)      #processing.getObjectFromUri()


        #=======================================================================
        #     #---QGIS 3 API version. Added QgsRuleBasedLabeling
        # root = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
        #=======================================================================
        progress.setText('<b>Generate xml for</b>')
        rules_xml=""
        for idx,field in enumerate(_label_fields_):
            progress.setText('\t{}'.format(field))
            rule_xml=self.TMPL_RULE.format(_name_='Line_{}'.format(idx)
                                           ,_filter_=''
                                           , _rnd12_=int(random.random()*1000000000000)#random.randint(1000000000000,999999999999)
                                           #, _field_=" makeMultilineFormatedLabel({fld},{pos},{size} )".format(fld=field, pos=idx, size=len(_label_fields_) )
                                           , _field_=self.makeMultilineFormatedLabel(field, idx,len(_label_fields_) )
                                           , _is_expression_=1
                                           )
            rules_xml+=rule_xml
        
        #=======================================================================
        #     #---QGIS 3 API version. Added QgsRuleBasedLabeling
        #     #Configure label settings
        #     settings = QgsPalLayerSettings()
        #     settings.fieldName = _label_fields_
        #     textFormat = QgsTextFormat()
        #     textFormat.setSize(10)
        #     settings.setFormat(textFormat)
        #     #create and append a new rule
        #     rule = QgsRuleBasedLabeling.Rule(settings)
        #     rule.setDescription(fieldName)
        #     #rule.setFilterExpression('myExpression')
        #     root.appendChild(rule)
        # #Apply label configuration
        # rules = QgsRuleBasedLabeling(root)
        # Layer_to_update.setLabeling(rules)
        #=======================================================================
        rules_xml=self.TMPL_RULES.format(_rule_=rules_xml
                                         ,_rnd12_=int(random.random()*1000000000000)#random.randint(1000000000000,999999999999)
                                         )
        progress.setText('<b>Store xml as style</b>')
        f = NamedTemporaryFile(delete=False)
        f.write(rules_xml)
        f.flush()
        f.close()      
        progress.setText('<b>Loading style {}</b>'.format(f.name))
        #editLayerStyles=Layer_to_update.styleManager()
        #editLayerStyles.addStyle( name, editLayerStyles.style(editLayerStyles.styles()[0]) ) 
        #editLayerStyles.setCurrentStyle(name)
        Layer_to_update.loadNamedStyle(f.name)        
        Layer_to_update.triggerRepaint()
        progress.setText('<b>End</b>')
        
                    
        