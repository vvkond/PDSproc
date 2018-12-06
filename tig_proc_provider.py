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

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from tig_proc_algorithm             import TigSurfitAlgorithm
from tig_proc_merge                 import TigMergeLayersAlgorithm
from tig_proc_contours              import TigContouringAlgorithm
from tig_proc_triangle              import TigTriangleAlgorithm
from tig_proc_reservesByRaster      import TigReservesByRasterAlgorithm
from tig_proc_correction            import TigSurfaceCorrectionAlgorithm
from tig_proc_surfIntersection      import TigSurfaceIntersectCorrectAlgorithm
from tig_proc_reservesVolume        import TigVolumeMethodAlgorithm
from tig_proc_upd_point_locaion     import TigUpdatePointLocationAlgorithm
from tig_proc_set_custom_prop       import TigSetCustomProp 


class TigSurfitProvider(AlgorithmProvider):
    TIG_GRIDDING_SETTING = 'TIG_GRIDDING_SETTING'

    def __init__(self):
        AlgorithmProvider.__init__(self)

        # Load algorithms
        self.alglist = [
                        TigSurfitAlgorithm(), TigMergeLayersAlgorithm(),
                        TigContouringAlgorithm(), TigTriangleAlgorithm(),
                        TigReservesByRasterAlgorithm(),
                        TigSurfaceCorrectionAlgorithm(),
                        TigSurfaceIntersectCorrectAlgorithm(),
                        TigVolumeMethodAlgorithm(),
                        TigUpdatePointLocationAlgorithm(),
                        TigSetCustomProp()
                        ]

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
