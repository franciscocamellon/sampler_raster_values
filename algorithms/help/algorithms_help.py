# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CreatePointsFromFileAlgorithm
                                 A QGIS plugin
 Amostra valores de pixels a partir de rasters e preenche atributos no QGIS.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-10-27
        copyright            : (C) 2023 by Francisco Camello
        email                : camelloncase@gmail.com
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

__author__ = 'Francisco Camello'
__date__ = '2023-11-20'
__copyright__ = '(C) 2023 by CamellOnCase'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import json
import os


class HTMLHelpCreator(object):

    @staticmethod
    def shortHelpString(algorithm_name):
        html_path = "{}/{}.html".format(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html'),
                                        algorithm_name)

        html_file = open(html_path, "r")
        html_string = html_file.read()

        return html_string
