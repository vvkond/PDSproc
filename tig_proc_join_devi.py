# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2018-12-03'
__copyright__ = '(C) 2018 by Alex Russkikh'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from PyQt4.QtCore import QSettings, QProcess, QVariant
from qgis.utils   import iface
from qgis.core    import *

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
def qgs_get_last_child_rules(rule):
    childrenRules=rule.children()
    res=[]
    if len(childrenRules)>0:
        for childrenRule in childrenRules:
            res.extend(qgs_get_last_child_rules(childrenRule))
    else:
        res=[rule]
    return res
#===============================================================================
# 
#===============================================================================
def qgs_get_all_rules(rule):
    childrenRules=rule.children()
    res=[rule]
    if len(childrenRules)>0:
        for childrenRule in childrenRules:
            res.extend(qgs_get_all_rules(childrenRule))
    else:
        pass
    return res
#===============================================================================
# 
#===============================================================================
class TigJoinDeviLayersAlgorithm(GeoAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    FIELD_JOIN_TO="FIELD_A"
    
    LAYER_FROM="LAYER_FROM"
    FIELD_JOIN_FROM="FIELD_B"
    
    FIELD_TO_JOIN="FIELD_TO_JOIN"
    PREFIX="PREFIX"
    
    USE_CACHE="USE_CACHE"
    
    ENABLE_DEVI="ENABLE_DEVI"
    ENABLE_DEVI_ST="ENABLE_DEVI_ST"
    ENABLE_DEVI_END="ENABLE_DEVI_END"
    ENABLE_DEVI_LINE="ENABLE_DEVI_LINE"
    
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
        self.name = u'Join devi layer'
        self.i18n_name = u'Подключение слоя инклинометрии'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        
        #---------------LAYER A
        self.addParameter(
            ParameterVector(
                self.LAYER_TO  #layer id
                , self.tr('Layer to update') #display text
                , [ParameterVector.VECTOR_TYPE_POINT,ParameterVector.VECTOR_TYPE_LINE] #layer types
                , False #[is Optional?]
                ))
        
        self.addParameter(
            ParameterTableField(
                self.FIELD_JOIN_TO #id
                , self.tr('Field for join layers in A(default well_id)') #display text
                , self.LAYER_TO #field layer
                , ParameterTableField.DATA_TYPE_ANY
                , True #[is Optional?]
                ))

        #---------------LAYER B
        self.addParameter(
            ParameterVector(
                self.LAYER_FROM  #layer id
                , self.tr('Devi layer') #display text
                , [ParameterVector.VECTOR_TYPE_POINT,ParameterVector.VECTOR_TYPE_LINE] #layer types
                , False #[is Optional?]
                ))
        
        self.addParameter(
            ParameterTableField(
                self.FIELD_JOIN_FROM #id
                , self.tr('Field to join devi layer(default well_id)') #display text
                , self.LAYER_FROM #field layer
                , ParameterTableField.DATA_TYPE_ANY
                , True #[is Optional?]
                ))

        self.addParameter(
            ParameterTableField(
                self.FIELD_TO_JOIN #id
                , self.tr('Field with devi WKT') #display text
                , self.LAYER_FROM #field layer
                , ParameterTableField.DATA_TYPE_ANY
                , False #[is Optional?]
                ))
        
        self.addParameter(
            ParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                self.PREFIX    #name
                , u'Префикс' #desc
                , '_' #default
                , False # is big text?
                , False
                #, False #for 2.14
                ))
        #---------------
        self.addParameter(
            ParameterBoolean(
                self.ENABLE_DEVI #id
                , self.tr('Enable devi?') #display text
                , True #default
                ))
        self.addParameter(
            ParameterBoolean(
                self.ENABLE_DEVI_ST #id
                , self.tr('Add devi start point?') #display text
                , True #default
                ))
        self.addParameter(
            ParameterBoolean(
                self.ENABLE_DEVI_LINE #id
                , self.tr('Add devi line?') #display text
                , True #default
                ))
        self.addParameter(
            ParameterBoolean(
                self.ENABLE_DEVI_END #id
                , self.tr('Add devi end point?') #display text
                , True #default
                ))
        #---------------
        self.addParameter(
            ParameterBoolean(
                self.USE_CACHE #id
                , self.tr('Save in cache?') #display text
                , True #default
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
        Layer_from_update   = self.getParameterValue(self.LAYER_FROM)
        
        _joinfield__to   = self.getParameterValue(self.FIELD_JOIN_TO)
        _joinfield__from = self.getParameterValue(self.FIELD_JOIN_FROM)
        
        _join_what       = self.getParameterValue(self.FIELD_TO_JOIN)
        _prefix          = self.getParameterValue(self.PREFIX)
        
        _use_cache       = self.getParameterValue(self.USE_CACHE)
        _enable_devi       =self.getParameterValue(self.ENABLE_DEVI     )
        _enable_devi_st    =self.getParameterValue(self.ENABLE_DEVI_ST  )
        _enable_devi_end   =self.getParameterValue(self.ENABLE_DEVI_END )
        _enable_devi_line  =self.getParameterValue(self.ENABLE_DEVI_LINE)
         
        #--- create virtual field with geometry
        Layer_from_update=dataobjects.getObject(Layer_from_update)  #processing.getObjectFromUri()
        Layer_to_update=dataobjects.getObject(Layer_to_update)      #processing.getObjectFromUri()
        
        _joinfield__from='well_id' if _joinfield__from is None else _joinfield__from
        _joinfield__to=  'well_id' if _joinfield__to   is None else _joinfield__to
        
        #Layer_from_update.startEditing()
        #cX = QgsField( '_x', QVariant.Double  )
        #cY = QgsField( '_y', QVariant.Double  )
        #cGeometry= QgsField( '_geometry', QVariant.String  )
        #--- VIRTUAL FIELD
        #Layer_from_update.addExpressionField( 'x(start_point($geometry))' , cX )
        #Layer_from_update.addExpressionField( 'y(start_point($geometry))' , cY )
        #Layer_from_update.addExpressionField( ' geom_to_wkt( $geometry )' , cGeometry )
        #Layer_from_update.commitChanges()
        
        #--- remove layers join
        progress.setText('Try remove old join <b>{}</b> -> <b>{}</b>'.format(Layer_to_update.id(),Layer_from_update.id()))
        Layer_to_update.removeJoin( Layer_from_update.id() )
        #--- join layers. Join only virtual field  'upd_coord_geometry'
        progress.setText('Join: \n\t{} \n\t-> \n\t{}'.format(Layer_to_update.id(),Layer_from_update.id()))
        joinObject = QgsVectorJoinInfo()
        joinObject.joinLayerId = Layer_from_update.id()
        joinObject.joinFieldName = _joinfield__from
        joinObject.targetFieldName = _joinfield__to
        joinObject.memoryCache = _use_cache
        joinObject.prefix=_prefix
        joinObject.setJoinFieldNamesSubset([_join_what])
        Layer_to_update.addJoin(joinObject)
        
        
        layerCurrentStyleRendere=Layer_to_update.rendererV2()
        if type(layerCurrentStyleRendere)==QgsRuleBasedRendererV2:
            rootRule=layerCurrentStyleRendere.rootRule()
            #----search rule by desc and remove it. After remove need reread all rules again
            progress.setText('<b>Remove old devi symbols</b>')
            while True:
                isRuleRemoved=False
                for rule in qgs_get_all_rules(rootRule):
                    if rule.description().split(".")[0]==u'devi':
                        progress.setText('<b>Remove rule {}->{}</b>'.format(rule.parent().label(),rule.label()))
                        rule.parent().removeChild(rule)
                        isRuleRemoved=True
                        break
                if not isRuleRemoved:break
            #---refresh layer in LEGEND
            progress.setText('<b>Refresh layer in legend</b>')
            Layer_to_update.setRendererV2(layerCurrentStyleRendere)
            Layer_to_update.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(Layer_to_update.id())
            #------ITERATE OVER LAYER STYLE-RULES    
            # Rule->Symbol->SymbolLayer            
            for rule in qgs_get_last_child_rules(rootRule):
                #------ skeep diagram Bubble rule
                isGoNext=False
                rulesymbols=rule.symbol() if isinstance(rule.symbol(),(list,)) else [rule.symbol()]
                for symb in rulesymbols:
                    if symb is None:continue
                    rulesymbolslayer=symb.symbolLayers()  if isinstance(symb.symbolLayers(),(list,)) else [symb.symbolLayers()]
                    for symblayer in rulesymbolslayer:
                        if symblayer is None:continue
                        #if type(symblayer)==BubbleSymbolLayer:
                        if str(symblayer.__class__)=="<class 'QgisPDS.qgis_pds_prodRenderer.BubbleSymbolLayer'>":
                            isGoNext=True
                            break
                if isGoNext:continue
                            
                
                #------
                progress.setText('<b>Rule:{}</b>'.format(str(rule)))
                #------ add GROUP
                new_grp_rule = QgsRuleBasedRendererV2.Rule(None)
                new_grp_rule.setLabel(u'инклинометрия')
                new_grp_rule.setDescription(u'devi.Dont replace it')
                new_grp_rule.setActive(_enable_devi)
                #new_grp_rule.setRuleKey(u'devi')  # --- ID OF DEVI GRP   rootRule.removeChild(rootRule.findRuleByKey(u'its rule key')) MUST BE UNIQUE
                #---------УСТЬЕ
                if _enable_devi_st:
                    symbolLayer = QgsGeometryGeneratorSymbolLayerV2.create()
                    symbolLayer.setGeometryExpression(' start_point( geom_from_wkt( "{}{}" ))'.format(_prefix,_join_what))  #  end_point(  geom_from_wkt( "_devi" ))
                    symbolLayer.setSymbolType(QgsSymbolV2.Marker)
                    sub_symbol=QgsMarkerSymbolV2.createSimple({
                                                   'name': 'circle'
                                                 , 'outline_color': "227,26,28,255"
                                                 , 'outline_style':'solid'
                                                 , 'outline_width_unit':'MM'
                                                 , 'outline_width': '0'
                                                 , 'scale_method':'diameter'
                                                 , 'size_unit':'MM'
                                                 , 'color': "255,0,0,0"
                                                 , 'offset': '0,0'
                                                 , 'angle':'0'
                                                 , 'size':'2'
                                                })
                    symbolLayer.setSubSymbol(sub_symbol)
                    symbol = QgsMarkerSymbolV2([symbolLayer.clone()])  #---need clone!!! or take error when create again symbolLayer /symbol  
                    sub_rule = QgsRuleBasedRendererV2.Rule(symbol)
                    sub_rule.setLabel(u"устье")
                    sub_rule.setDescription(u'devi_start.Dont replace it')
                    sub_rule.setActive(True)
                    #sub_rule.setRuleKey(u'devi_start')   # MUST BE UNIQUE
                    sub_rule.setFilterExpression(u'') 
                    new_grp_rule.appendChild(sub_rule.clone())         #---need clone!!! or take error when create again symbolLayer /symbol
                #---------СТВОЛ
                if _enable_devi_line:
                    symbolLayer = QgsGeometryGeneratorSymbolLayerV2.create()
                    symbolLayer.setGeometryExpression(' geom_from_wkt( "{}{}" )'.format(_prefix,_join_what))
                    symbolLayer.setSymbolType(QgsSymbolV2.Line)
                    sub_symbol=QgsLineSymbolV2.createSimple({
                                                   'line_color': "0,0,0,255"
                                                 , 'line_width':'0.26'
                                                 , 'line_width_unit':'MM'
                                                 , 'capstyle':'square'
                                                 , 'line_style':'solid'
                                                 , 'joinstyle':'bevel'
                                                 , 'draw_inside_polygon':'0'
                                                 , 'use_custom_dash':'0'
                                                })
                    symbolLayer.setSubSymbol(sub_symbol)
                    symbol = QgsMarkerSymbolV2([symbolLayer.clone()])  #---need clone!!! or take error when create again symbolLayer /symbol                  
                    sub_rule = QgsRuleBasedRendererV2.Rule(symbol)
                    sub_rule.setLabel(u"ствол")
                    sub_rule.setDescription(u'devi_line.Dont replace it')
                    sub_rule.setActive(True)
                    #sub_rule.setRuleKey(u'devi_line')   # MUST BE UNIQUE
                    sub_rule.setFilterExpression(u'') 
                    new_grp_rule.appendChild(sub_rule.clone())        #---need clone!!! or take error when create again symbolLayer /symbol
                #---------ЗАБОЙ
                if _enable_devi_end:
                    symbolLayer = QgsGeometryGeneratorSymbolLayerV2.create()
                    symbolLayer.setGeometryExpression(' end_point( geom_from_wkt( "{}{}" ))'.format(_prefix,_join_what))  #  end_point(  geom_from_wkt( "_devi" ))
                    symbolLayer.setSymbolType(QgsSymbolV2.Marker)
                    sub_symbol=QgsMarkerSymbolV2.createSimple({
                                                   'name': 'circle'
                                                 , 'outline_color': "0.0.0.255"
                                                 , 'outline_style':'solid'
                                                 , 'outline_width_unit':'MM'
                                                 , 'scale_method':'diameter'
                                                 , 'size_unit':'MM'
                                                 , 'color': "255,0,0,0"
                                                 , 'offset': '0,0'
                                                 , 'angle':'0'
                                                 , 'size':'1'
                                                })
                    symbolLayer.setSubSymbol(sub_symbol)
                    symbol = QgsMarkerSymbolV2([symbolLayer.clone()])  #---need clone!!! or take error when create again symbolLayer /symbol  
                    sub_rule = QgsRuleBasedRendererV2.Rule(symbol)
                    sub_rule.setLabel(u"забой")
                    sub_rule.setDescription(u'devi_end.Dont replace it')
                    sub_rule.setActive(True)
                    #sub_rule.setRuleKey(u'devi_start')   # MUST BE UNIQUE
                    sub_rule.setFilterExpression(u'') 
                    new_grp_rule.appendChild(sub_rule.clone())         #---need clone!!! or take error when create again symbolLayer /symbol
                    
                #---------Добавляем новое правило под текущее 
                rule.appendChild(new_grp_rule.clone())            #---need clone!!! or take error when create again symbolLayer /symbol

            #---refresh layer in LEGEND
            progress.setText('<b>Refresh layer in legend</b>')
            Layer_to_update.setRendererV2(layerCurrentStyleRendere)
            Layer_to_update.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(Layer_to_update.id())
                
        else:
            progress.setText('<b>Error.Allowed only QgsRuleBasedRendererV2 style</b>')

        progress.setText('<b>End</b>')
        return Layer_to_update
        
        
        
        
                    
        