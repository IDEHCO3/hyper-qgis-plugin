# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IBGEVisualizer
                                 A QGIS plugin
 Acesso ao Visualizer
                             -------------------
        begin                : 2018-06-01
        copyright            : (C) 2018 by IBGE
        email                : andre.censitario@ibge.gov.br
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
    """Load IBGEVisualizer class from file IBGEVisualizer.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """

    from ibge_visualizer import IBGEVisualizer as ibge

    return ibge(iface)
