# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProbabilisticMapAlgebraTool
                                 A QGIS plugin
 Plug-in to apply Bayesian belief networks on spatial data
                             -------------------
        begin                : 2014-12-03
        copyright            : (C) 2014 by Dries Landuyt
        email                : drieslanduyt@gmail.com
        git sha              : $Format:%H$
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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ProbabilisticMapAlgebraTool class from file ProbabilisticMapAlgebraTool.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .probabilistic_map_algebra_tool import ProbabilisticMapAlgebraTool
    return ProbabilisticMapAlgebraTool(iface)
