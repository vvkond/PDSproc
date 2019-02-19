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
from processing.core.parameters import ParameterFile
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter



#===============================================================================
# 
#===============================================================================
class TigSetMapVariable(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    
    @see: https://www.mdpi.com/2220-9964/4/4/2219/htm

    @var var: 
        00    str: PROP_1    
        01    str: __doc__    
        02    str: __init__    
        03    str: __module__    
        04    str: __str__    
        05    str: _checkParameterValuesBeforeExecuting    
        06    str: _formatHelp    
        07    str: _icon    
        08    str: addOutput    
        09    str: addParameter    
        10    str: allowOnlyOpenedLayers    
        11    str: canRunInBatchMode    
        12    str: checkBeforeOpeningParametersDialog    
        13    str: checkInputCRS    
        14    str: checkOutputFileExtensions    
        15    str: checkParameterValuesBeforeExecuting    
        16    str: commandLineName    
        17    str: convertUnsupportedFormats    
        18    str: crs    
        19    str: defineCharacteristics    
        20    str: displayName    
        21    str: displayNames    
        22    str: execute    
        23    str: getAsCommand    
        24    str: getCopy    
        25    str: getCustomModelerParametersDialog    
        26    str: getCustomParametersDialog    
        27    str: getDefaultIcon    
        28    str: getFormatShortNameFromFilename    
        29    str: getHTMLOutputsCount    
        30    str: getIcon    
        31    str: getOutputFromName    
        32    str: getOutputValue    
        33    str: getOutputValuesAsDictionary    
        34    str: getParameterDescriptions    
        35    str: getParameterFromName    
        36    str: getParameterValue    
        37    str: getVisibleOutputsCount    
        38    str: getVisibleParametersCount    
        39    str: group    
        40    str: help    
        41    str: i18n_group    
        42    str: i18n_name    
        43    str: model    
        44    str: name    
        45    str: outputs    
        46    str: parameters    
        47    str: processAlgorithm    
        48    str: provider    
        49    str: removeOutputFromName    
        50    str: resolveDataObjects    
        51    str: resolveTemporaryOutputs    
        52    str: runHookScript    
        53    str: runPostExecutionScript    
        54    str: runPreExecutionScript    
        55    str: setOutputCRS    
        56    str: setOutputValue    
        57    str: setParameterValue    
        58    str: shortHelp    
        59    str: showInModeler    
        60    str: showInToolbox    
        61    str: tr    
        62    str: trAlgorithm    
    
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PROPS=[
        ["company_name",u'Имя компании',u''    ,ParameterString]
        ,["project"    ,u'Имя проекта',u''     ,ParameterString]
        ,["map_date"   ,u'Дата для штампа',u'' ,ParameterString]
        ,["emblem"     ,u'Файл с эмблемой',u'' ,ParameterString]
        ]

    #QgsExpressionContextUtils.projectScope().variable(PROP_1)
    #QgsExpressionContextUtils.setProjectVariable(PROP_1,self.getParameterValue(self.PROP_1)) 
    #===========================================================================
    # 
    #===========================================================================
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # The name that the user will see in the toolbox
        self.name = self.tr(u'Set map variable')
        self.i18n_name = u'Задание переменных карты'

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr(u'Tools')

        for [name,desc,default,paramtype] in self.PROPS:
            if paramtype==ParameterString:
                self.addParameter(
                    ParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                        name
                        , desc
                        , default
                        , False # is big text?
                        , False
                        #, False #for 2.14
                        ))
            elif paramtype==ParameterFile:
                self.addParameter(
                    ParameterFile(
                        name=name
                        , description=desc
                        , isFolder=False
                        , optional=True
                        , ext=None
                        ))
            else:
                raise Exception('Unknown type parameter')
    #===================================================================
    # 
    #===================================================================
    def checkBeforeOpeningParametersDialog(self):
        # self.parameters[0]
        # ESCAPED_NEWLINE', 'NEWLINE', '__doc__', '__init__', '__module__', '__str__', 'default', 'description'
        #'evaluateExpressions', 'getAsScriptCode', 'getValueAsCommandLineParameter', 'hidden', 'isAdvanced', 'multiline', 'name', 'optional', 'setDefaultValue', 'setValue', 'todict', 'tr', 'typeName', 'value'
        #param.setValue(QgsExpressionContextUtils.projectScope().variable(self.PROP_1))
        for [name,desc,default,paramtype] in self.PROPS:
                param=self.getParameterFromName(name)   
                if paramtype==ParameterString:
                    param.default=QgsExpressionContextUtils.projectScope().variable(name)
                else:
                    pass
    
    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        for [name,desc,default,paramtype] in self.PROPS:
            QgsExpressionContextUtils.setProjectVariable(name, self.getParameterValue(name)  )
        pass
  
        
  
        