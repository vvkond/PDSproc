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
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter


class TigUpdatePointLocationAlgorithm(GeoAlgorithm):
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

    LAYER_A="LAYER_A"
    FIELD_TO_JOIN_A="FIELD_A"
    LAYER_B="LAYER_B"
    FIELD_TO_JOIN_B="FIELD_B"

##Field_for_join_to=optional field Layer_to_update
##Field_for_join_from=optional field Layer_from_update


    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = self.tr(u'Update well location')
        self.i18n_name = u'Обновление расположения скважин'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(
            ParameterVector(
                self.LAYER_A  #layer id
                , self.tr('Layer to update') #display text
                , [ParameterVector.VECTOR_TYPE_POINT] #layer types
                , False #[is Optional?]
                ))
        
        self.addParameter(
            ParameterTableField(
                self.FIELD_TO_JOIN_A #id
                , self.tr('Field for join layers in A(default well_id)') #display text
                , self.LAYER_A #field layer
                , ParameterTableField.DATA_TYPE_ANY
                , True #[is Optional?]
                ))

        self.addParameter(
            ParameterVector(
                self.LAYER_B  #layer id
                , self.tr('Layer from update') #display text
                , [ParameterVector.VECTOR_TYPE_POINT] #layer types
                , False #[is Optional?]
                ))
        
        self.addParameter(
            ParameterTableField(
                self.FIELD_TO_JOIN_B #id
                , self.tr('Field to for layers in B(default well_id)') #display text
                , self.LAYER_B #field layer
                , ParameterTableField.DATA_TYPE_ANY
                , True #[is Optional?]
                ))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        Layer_to_update = self.getParameterValue(self.LAYER_A)
        Layer_from_update = self.getParameterValue(self.LAYER_B)
        Field_for_join_to = self.getParameterValue(self.FIELD_TO_JOIN_A)
        Field_for_join_from = self.getParameterValue(self.FIELD_TO_JOIN_B)

        #--- create virtual field with geometry
        Layer_from_update=dataobjects.getObject(Layer_from_update)  #processing.getObjectFromUri()
        Layer_to_update=dataobjects.getObject(Layer_to_update)      #processing.getObjectFromUri()
        
        Field_for_join_from='well_id' if Field_for_join_from is None else Field_for_join_from
        Field_for_join_to='well_id' if Field_for_join_to is None else Field_for_join_to
        #Layer_from_update.startEditing()
        #cX = QgsField( '_x', QVariant.Double  )
        #cY = QgsField( '_y', QVariant.Double  )
        cGeometry= QgsField( '_geometry', QVariant.String  )
        #--- VIRTUAL FIELD
        #Layer_from_update.addExpressionField( 'x(start_point($geometry))' , cX )
        #Layer_from_update.addExpressionField( 'y(start_point($geometry))' , cY )
        Layer_from_update.addExpressionField( ' geom_to_wkt( $geometry )' , cGeometry )
        #Layer_from_update.commitChanges()
        
        #--- remove layers join
        Layer_to_update.removeJoin( Layer_from_update.id() )
        #--- join layers. Join only virtual field  'upd_coord_geometry'
        joinObject = QgsVectorJoinInfo()
        joinObject.joinLayerId = Layer_from_update.id()
        joinObject.joinFieldName = Field_for_join_from
        joinObject.targetFieldName = Field_for_join_to
        joinObject.memoryCache = True
        joinObject.prefix='upd_coord'
        joinObject.setJoinFieldNamesSubset(['_geometry'])
        Layer_to_update.addJoin(joinObject)
        #---copy filter expression
        filter_exp=Layer_to_update.subsetString()
        Layer_to_update.setSubsetString('')
        #--- update geometry from field 'upd_coord_geometry'
        Layer_to_update.startEditing()
        e = QgsExpression( 'if( geom_from_wkt(  "upd_coord_geometry" )  IS  None, $geometry ,geom_from_wkt(  "upd_coord_geometry" ))' )
        e.prepare( Layer_to_update.pendingFields() )
        for feature in Layer_to_update.getFeatures():
            Layer_to_update.dataProvider().changeGeometryValues({feature.id(): e.evaluate( feature )})
        Layer_to_update.beginEditCommand("edit")
        Layer_to_update.endEditCommand()
        Layer_to_update.commitChanges()
        #--- restore filter expression
        Layer_to_update.setSubsetString(filter_exp)
        #--- remove layers join
        Layer_to_update.removeJoin( Layer_from_update.id() )
        
                    
    def script():
        return """
##Layer_to_update=vector point
##Field_for_join_to=optional field Layer_to_update
##Layer_from_update=vector point
##Field_for_join_from=optional field Layer_from_update
##General Tools=group
##Move point =name

from qgis.core import *
from PyQt4.QtCore import QVariant

#--- create virtual field with geometry
Layer_from_update=processing.getObject(Layer_from_update)
Layer_to_update=processing.getObject(Layer_to_update)

Field_for_join_from='well_id' if Field_for_join_from is None else Field_for_join_from
Field_for_join_to='well_id' if Field_for_join_to is None else Field_for_join_to
#Layer_from_update.startEditing()
#cX = QgsField( '_x', QVariant.Double  )
#cY = QgsField( '_y', QVariant.Double  )
cGeometry= QgsField( '_geometry', QVariant.String  )
#--- VIRTUAL FIELD
#Layer_from_update.addExpressionField( 'x(start_point($geometry))' , cX )
#Layer_from_update.addExpressionField( 'y(start_point($geometry))' , cY )
Layer_from_update.addExpressionField( ' geom_to_wkt( $geometry )' , cGeometry )
#Layer_from_update.commitChanges()

#--- remove layers join
Layer_to_update.removeJoin( Layer_from_update.id() )
#--- join layers. Join only virtual field  'upd_coord_geometry'
joinObject = QgsVectorJoinInfo()
joinObject.joinLayerId = Layer_from_update.id()
joinObject.joinFieldName = Field_for_join_from
joinObject.targetFieldName = Field_for_join_to
joinObject.memoryCache = True
joinObject.prefix='upd_coord'
joinObject.setJoinFieldNamesSubset(['_geometry'])
Layer_to_update.addJoin(joinObject)
#---copy filter expression
filter_exp=Layer_to_update.subsetString()
Layer_to_update.setSubsetString('')
#--- update geometry from field 'upd_coord_geometry'
Layer_to_update.startEditing()
e = QgsExpression( 'if( geom_from_wkt(  "upd_coord_geometry" )  IS  None, $geometry ,geom_from_wkt(  "upd_coord_geometry" ))' )
e.prepare( Layer_to_update.pendingFields() )
for feature in Layer_to_update.getFeatures():
    Layer_to_update.dataProvider().changeGeometryValues({feature.id(): e.evaluate( feature )})
Layer_to_update.beginEditCommand("edit")
Layer_to_update.endEditCommand()
Layer_to_update.commitChanges()
#--- restore filter expression
Layer_to_update.setSubsetString(filter_exp)
#--- remove layers join
Layer_to_update.removeJoin( Layer_from_update.id() )

"""
        