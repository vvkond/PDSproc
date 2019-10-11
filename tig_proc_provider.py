# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TigSurfit
                                 A QGIS plugin
 Gridding with Surfit
                              -------------------
        begin                : 2017-05-08
        copyright            : (C) 2017 by Viktor Kondrashov
        email                : viktor@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
import importlib
from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os


def load_class(full_class_string,on_except=None):
    """
    dynamically load a class from a string
    """
    try:
        class_data = full_class_string.split(".")
        module_path = ".".join(class_data[:-1])
        class_str = class_data[-1]
        module = importlib.import_module(module_path)
        # Finally, we retrieve the Class
        return getattr(module, class_str)
    except Exception as e:
        QtGui.QMessageBox.critical(None, u'Error', str(e), QtGui.QMessageBox.Ok)  
        if on_except is not None:
            return on_except
        else:
            raise e 


TigSurfitAlgorithm                      =load_class('PDSproc.tig_proc_algorithm.TigSurfitAlgorithm'                                    ,on_except=lambda:None)
#TigMergeLayersAlgorithm                 =load_class('PDSproc.tig_proc_merge.TigMergeLayersAlgorithm'                                   ,on_except=lambda:None)
TigContouringAlgorithm                  =load_class('PDSproc.tig_proc_contours.TigContouringAlgorithm'                                 ,on_except=lambda:None)
TigTriangleAlgorithm                    =load_class('PDSproc.tig_proc_triangle.TigTriangleAlgorithm'                                   ,on_except=lambda:None)
TigReservesByRasterAlgorithm            =load_class('PDSproc.tig_proc_reservesByRaster.TigReservesByRasterAlgorithm'                   ,on_except=lambda:None)
TigSurfaceCorrectionAlgorithm           =load_class('PDSproc.tig_proc_correction.TigSurfaceCorrectionAlgorithm'                        ,on_except=lambda:None)
TigSurfaceIntersectCorrectAlgorithm     =load_class('PDSproc.tig_proc_surfIntersection.TigSurfaceIntersectCorrectAlgorithm'            ,on_except=lambda:None)
TigVolumeMethodAlgorithm                =load_class('PDSproc.tig_proc_reservesVolume.TigVolumeMethodAlgorithm'                         ,on_except=lambda:None)
TigUpdatePointLocationAlgorithm         =load_class('PDSproc.tig_proc_upd_point_locaion.TigUpdatePointLocationAlgorithm'               ,on_except=lambda:None)
TigSetCustomProp                        =load_class('PDSproc.tig_proc_set_custom_prop.TigSetCustomProp'                                ,on_except=lambda:None)
TigSetPdsCustomProp                     =load_class('PDSproc.tig_proc_set_pds_custom_prop.TigSetPdsCustomProp'                         ,on_except=lambda:None)
TigUpdateLabelLocationAlgorithm         =load_class('PDSproc.tig_proc_upd_lbl_locaion.TigUpdateLabelLocationAlgorithm'                 ,on_except=lambda:None)
TigUpdateTableFieldAlgorithm            =load_class('PDSproc.tig_proc_upd_table_field.TigUpdateTableFieldAlgorithm'                    ,on_except=lambda:None)
TigCreateMultilineRuleLabelAlgorithm    =load_class('PDSproc.tig_proc_createMultilineRuledLabel.TigCreateMultilineRuleLabelAlgorithm'  ,on_except=lambda:None)
TigSetMapVariable                       =load_class('PDSproc.tig_proc_set_map_variable.TigSetMapVariable'                              ,on_except=lambda:None) 
TigShowRuleLabelContours                =load_class('PDSproc.tig_proc_showRuledContours.TigShowRuleLabelContours'                      ,on_except=lambda:None)
TigJoinLayersAlgorithm                  =load_class('PDSproc.tig_proc_join_layers.TigJoinLayersAlgorithm'                              ,on_except=lambda:None)
TigSwitchLayerStyleAlgorithm            =load_class('PDSproc.tig_proc_style_switch.TigSwitchLayerStyleAlgorithm'                       ,on_except=lambda:None)
TigJoinDeviLayersAlgorithm              =load_class('PDSproc.tig_proc_join_devi.TigJoinDeviLayersAlgorithm'                            ,on_except=lambda:None)


class TigSurfitProvider(AlgorithmProvider):
    TIG_GRIDDING_SETTING = 'TIG_GRIDDING_SETTING'

    def __init__(self):
        AlgorithmProvider.__init__(self)
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PDSproc_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        

        # Load algorithms
        try:
            self.alglist = [
                            TigSurfitAlgorithm() 
                            #,TigMergeLayersAlgorithm(), #use default QGIS ALG   processing.tools.general.runalg("qgis:mergevectorlayers")
                            ,TigContouringAlgorithm()
                            ,TigTriangleAlgorithm()
                            ,TigReservesByRasterAlgorithm()
                            ,TigSurfaceCorrectionAlgorithm()
                            ,TigSurfaceIntersectCorrectAlgorithm()
                            ,TigVolumeMethodAlgorithm()
                            ,TigUpdatePointLocationAlgorithm()
                            ,TigSetCustomProp()
                            ,TigSetPdsCustomProp()
                            ,TigUpdateLabelLocationAlgorithm()
                            ,TigUpdateTableFieldAlgorithm()
                            ,TigCreateMultilineRuleLabelAlgorithm()
                            ,TigSetMapVariable()
                            ,TigShowRuleLabelContours()
                            ,TigJoinLayersAlgorithm()
                            ,TigSwitchLayerStyleAlgorithm()
                            ,TigJoinDeviLayersAlgorithm()
                            ]
        except Exception as e:
            QtGui.QMessageBox.critical(None, u'Error', str(e), QtGui.QMessageBox.Ok)  

            
        self.alglist=filter(lambda alg:alg is not None, self.alglist)
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        """In this method we add settings needed to configure our
        provider.

        Do not forget to call the parent method, since it takes care
        or automatically adding a setting for activating or
        deactivating the algorithms in the provider.
        """
        AlgorithmProvider.initializeSettings(self)
        ProcessingConfig.addSetting(Setting('Pumaplus',
            TigSurfitProvider.TIG_GRIDDING_SETTING,
            'PUMA setting', 'Default value'))

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        AlgorithmProvider.unload(self)
        ProcessingConfig.removeSetting(
            TigSurfitProvider.TIG_GRIDDING_SETTING)

    def getName(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return "Pumaplus"

    def getDescription(self):
        """This is the provired full name.
        """
        return "Pumaplus"

    def getIcon(self):
        """We return the default icon.
        """
        return AlgorithmProvider.getIcon(self)

    def _loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        self.algs = self.alglist
