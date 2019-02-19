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
class TigSetPdsCustomProp(GeoAlgorithm):
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

    PROPS=[
         ["qgis_pds_type"]
        ,["pds_prod_SelectedReservoirs"]
        ,["pds_prod_PhaseFilter"]
        ]
    
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
        self.name = self.tr(u'Set selected layers pds custom properies')
        self.i18n_name = u'Задание свойств pds у выбранных слоев'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument

    #===================================================================
    # 
    #===================================================================
    def checkBeforeOpeningParametersDialog(self):
        # self.parameters[0]
        # ESCAPED_NEWLINE', 'NEWLINE', '__doc__', '__init__', '__module__', '__str__', 'default', 'description'
        #'evaluateExpressions', 'getAsScriptCode', 'getValueAsCommandLineParameter', 'hidden', 'isAdvanced', 'multiline', 'name', 'optional', 'setDefaultValue', 'setValue', 'todict', 'tr', 'typeName', 'value'
        #param.setValue(QgsExpressionContextUtils.projectScope().variable(self.PROP_1))
        self.parameters=[]
        self.param_info={}
        layers= iface.legendInterface().selectedLayers()
        for layer in layers:
            for [prop_name] in self.PROPS:
                self.addParameter(
                    ParameterString(  #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                        layer.id()+u"/"+prop_name #name 
                        , layer.name()+u" / "+prop_name #desc
                        , layer.customProperty(prop_name) #def
                        , False #mline
                        , True  #opt
                        #, False #for 2.14
                        ))
                self.param_info[layer.id()+u"/"+prop_name]=[layer,prop_name]
    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        for param_id,[Layer_to_update,prop_name] in self.param_info.items():
            Layer_to_update.setCustomProperty(prop_name, self.getParameterValue(param_id))
        pass
  
        
  
        