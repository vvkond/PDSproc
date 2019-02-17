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
from processing.core.parameters import ParameterString
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter

#===============================================================================
# 
#===============================================================================
class TigSetCustomProp(GeoAlgorithm):
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
    PROP_NAME="PROPERTY"
    PROP_VALUE="VALUE"

    #self.layer.setCustomProperty("qgis_pds_type", "pds_fond")
    #layer.customProperty("qgis_pds_type") 
    #===========================================================================
    # 
    #===========================================================================
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # The name that the user will see in the toolbox
        self.name = self.tr(u'Set custom property')
        self.i18n_name = u'Задание свойств слоя'

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
            ParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                self.PROP_NAME    #name
                , u'Имя свойства' #desc
                , 'qgis_pds_type/pds_prod_SelectedReservoirs/pds_prod_PhaseFilter/..' #default
                , False # is big text?
                , False
                #, False #for 2.14
                ))    
        self.addParameter(
            ParameterString(  #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                self.PROP_VALUE
                , u'Значение свойства'
                , 'pds_cumulative_production'
                , False 
                , False
                #, False #for 2.14
                ))

    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        Layer_to_update = self.getParameterValue(self.LAYER_A)
        Layer_to_update=dataobjects.getObject(Layer_to_update)  #processing.getObjectFromUri()
        Layer_to_update.setCustomProperty(self.getParameterValue(self.PROP_NAME), self.getParameterValue(self.PROP_VALUE))
        pass
  
        
  
        