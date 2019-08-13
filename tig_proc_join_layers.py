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
from processing.core.parameters import ParameterTableField,ParameterTableMultipleField
from processing.core.parameters import ParameterBoolean,ParameterString
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter

#===============================================================================
# 
#===============================================================================
class TigJoinLayersAlgorithm(GeoAlgorithm):
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
    
    FIELDS_TO_JOIN="FIELDS_TO_JOIN"
    PREFIX="PREFIX"
    
    USE_CACHE="USE_CACHE"

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
        self.name = self.tr(u'Join layers')
        self.i18n_name = u'Создание связей'

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
                , self.tr('Layer from update') #display text
                , [ParameterVector.VECTOR_TYPE_POINT,ParameterVector.VECTOR_TYPE_LINE] #layer types
                , False #[is Optional?]
                ))
        
        self.addParameter(
            ParameterTableField(
                self.FIELD_JOIN_FROM #id
                , self.tr('Field to for layers in B(default well_id)') #display text
                , self.LAYER_FROM #field layer
                , ParameterTableField.DATA_TYPE_ANY
                , True #[is Optional?]
                ))

        self.addParameter(
            ParameterTableMultipleField(
                self.FIELDS_TO_JOIN #id
                , self.tr('Fields to join') #display text
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
        
        _join_what_lst   = self.getParameterValue(self.FIELDS_TO_JOIN).split(";")
        _prefix          = self.getParameterValue(self.PREFIX)
        
        _use_cache       = self.getParameterValue(self.USE_CACHE)
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
        joinObject.setJoinFieldNamesSubset(_join_what_lst)
        Layer_to_update.addJoin(joinObject)
        progress.setText('<b>End</b>')
                    
        