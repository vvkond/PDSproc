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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TigSurfit class from file TigSurfit.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .tig_proc import TigSurfitPlugin
    return TigSurfitPlugin()
