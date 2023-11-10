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
__date__ = '2023-11-08'
__copyright__ = '(C) 2023 by CamellOnCase'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import csv
import pandas as pd
from pandas._libs.tslibs.timestamps import Timestamp

from qgis.PyQt.Qt import QVariant
from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsProject
from qgis.core import (QgsProcessing, QgsProcessingParameterEnum, QgsProcessingParameterString, QgsFeatureSink,
                       QgsProcessingOutputVectorLayer, QgsProcessingException,
                       QgsProcessingParameterVectorLayer, QgsProcessingParameterFile,
                       QgsProcessingAlgorithm, QgsProcessingParameterField, QgsProcessingParameterFeatureSink)

from ..services.layer_services import LayerService
from ..services.system_service import SystemService


class CreatePointsFromFileAlgorithm(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT_FILE = 'INPUT_FILE'
    INPUT_FILE = 'INPUT_FILE'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_FILE,
                self.tr('Points spreadsheet'),
                behavior=QgsProcessingParameterFile.File
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Point observations')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        layerService = LayerService()
        systemService = SystemService()

        inputFile = self.parameterAsFile(parameters, self.INPUT_FILE, context)

        # pointDataFrame = pd.read_excel(inputFile, converters={'Date': pd.to_datetime})
        pointDataFrame = pd.read_excel(inputFile, parse_dates=['Date'])


        fields = layerService.createFields(pointDataFrame.dtypes.to_dict())

        project = QgsProject.instance()
        project_crs = project.crs()

        (sink, destination_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, 1, project_crs)

        df = pointDataFrame.to_dict(orient='records')

        features = []
        for point in df:
            feature = QgsFeature(fields)

            for key, value in point.items():
                if isinstance(value, Timestamp):
                    # Convert Timestamp to QVariant.Date
                    date_value = value.to_pydatetime().date()

                    # print(date_value)
                    feature[key] = str(date_value)
                else:
                    feature[key] = value

            geometry = QgsGeometry.fromPointXY(QgsPointXY(point['Longitude'], point['Latitude']))
            feature.setGeometry(geometry)
            features.append(feature)

        total = 100.0 / len(features) if len(features) else 0

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: destination_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Create Points from File'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreatePointsFromFileAlgorithm()
