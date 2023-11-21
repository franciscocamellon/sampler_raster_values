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

import os
from datetime import datetime

import pandas as pd
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingParameterEnum, QgsProcessingParameterString, QgsProcessingException,
                       QgsProcessingParameterFile,
                       QgsProcessingAlgorithm)

from ..services.layer_services import LayerService
from ..services.system_service import SystemService
from .help.algorithms_help import HTMLHelpCreator as Helper

ID_LIST = []
OBSERVATION_DATE_LIST = []
START_DATE_LIST = []
END_DATE_LIST = []
VARIABLE_LIST = []
MINIMUM_LIST = []
MAXIMUM_LIST = []
MEDIAN_LIST = []
MEAN_LIST = []
STDDEV_LIST = []


class BatchSummarizedExtractorAlgorithm(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_FILE = 'INPUT_FILE'
    DATE_FIELD = 'DATE_FIELD'
    INPUT_FOLDER = 'INPUT_FOLDER'
    AQUA_MODIS_VARIABLE = 'AQUA_MODIS_VARIABLE'
    BAND_NUMBER = 'BAND_NUMBER'
    OUTPUT = 'OUTPUT'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'

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
            QgsProcessingParameterString(
                self.DATE_FIELD,
                self.tr('Date field'),
                defaultValue='Write the name of date field here',
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_FOLDER,
                self.tr('Images folder'),
                behavior=QgsProcessingParameterFile.Folder
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.BAND_NUMBER,
                self.tr('Raster band'),
                options=['1', '2', '3'],
                defaultValue=0,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.AQUA_MODIS_VARIABLE,
                self.tr('AQUA MODIS variable'),
                options=[self.tr('chlor_a - Chlorophyll concentration'),
                         self.tr('sst - Sea Surface Temperature (11 μ daytime)')],
                defaultValue=0,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.OUTPUT_FOLDER,
                self.tr('Output folder'),
                behavior=QgsProcessingParameterFile.Folder
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        layerService = LayerService()
        systemService = SystemService()

        inputFolder = self.parameterAsFile(parameters, self.INPUT_FOLDER, context)
        outputFolder = self.parameterAsFile(parameters, self.OUTPUT_FOLDER, context)
        inputFile = self.parameterAsFile(parameters, self.INPUT_FILE, context)
        aquaModisVariable = self.parameterAsInt(parameters, self.AQUA_MODIS_VARIABLE, context)
        bandNumber = self.parameterAsInt(parameters, self.BAND_NUMBER, context)
        dateField = self.parameterAsString(parameters, self.DATE_FIELD, context)

        pointDataFrame = pd.read_excel(inputFile, parse_dates=[dateField])
        pointDataFrame[dateField] = pd.to_datetime(pointDataFrame[dateField])

        pointDataFrame['FormattedDate'] = pointDataFrame[dateField].dt.strftime('%Y%m%d')

        variable = layerService.retrieveNetcdfVariable(aquaModisVariable)

        netcdfImages = systemService.filterFilesInDirectory(inputFolder, '.nc')
        total = 100.0 / len(netcdfImages) if len(netcdfImages) else 0
        counter = 0

        for current, imageFile in enumerate(netcdfImages):

            if feedback.isCanceled():
                raise QgsProcessingException(self.tr('\nProcessing cancelled by the user!\n'))

            startDate, endDate = systemService.getDateRange(imageFile)

            for observationDate in pointDataFrame['FormattedDate']:
                parsedObservationDate = systemService.formatDate(observationDate)

                if systemService.isDateWithinRange(parsedObservationDate, startDate, endDate):
                    counter += 1

                    rasterLayer = layerService.createNetcdfRaster(aquaModisVariable, imageFile,
                                                                  os.path.join(inputFolder, imageFile), True)

                    if rasterLayer is not None:

                        stats = layerService.getSummaryStatistics(rasterLayer, (bandNumber + 1), variable)
                        feedback.pushInfo(self.tr(f'File {os.path.basename(imageFile)}, processed!\n '))

                        ID_LIST.append(counter)
                        OBSERVATION_DATE_LIST.append(datetime.strptime(str(parsedObservationDate), '%Y-%m-%d').strftime('%d/%m/%y'))
                        START_DATE_LIST.append(datetime.strptime(str(startDate), '%Y-%m-%d').strftime('%d/%m/%y'))
                        END_DATE_LIST.append(datetime.strptime(str(endDate), '%Y-%m-%d').strftime('%d/%m/%y'))
                        VARIABLE_LIST.append(variable)
                        MINIMUM_LIST.append(stats['STATISTICS_MINIMUM'])
                        MAXIMUM_LIST.append(stats['STATISTICS_MAXIMUM'])
                        MEDIAN_LIST.append(stats['STATISTICS_MEAN'])
                        MEAN_LIST.append(stats['STATISTICS_MEDIAN'])
                        STDDEV_LIST.append(stats['STATISTICS_STDDEV'])

                        feedback.setProgress(int(current * total))

                    else:
                        raise QgsProcessingException(self.tr('\nInvalid raster!\n'))

        excelDictionary = {
            'id': ID_LIST,
            'Observation date': OBSERVATION_DATE_LIST,
            'Start date': START_DATE_LIST,
            'End date': END_DATE_LIST,
            'Variable': VARIABLE_LIST,
            'Minimum': MINIMUM_LIST,
            'Maximum': MAXIMUM_LIST,
            'Median': MEDIAN_LIST,
            'Mean': MEAN_LIST,
            'Stddev': STDDEV_LIST
        }

        outputPath = os.path.join(outputFolder, 'Summarized values.csv')

        excelDataFrame = pd.DataFrame.from_dict(excelDictionary)
        excelDataFrame.to_csv(outputPath, sep=';', index=False, decimal=',')

        layerService.loadNonSpatialLayer(outputPath, 'Summarized values')

        return {self.OUTPUT: None}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'batch_summarized_values_extractor'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Batch Summarized Values Extractor')

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
        return 'Extraction'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return Helper.shortHelpString(self.name())

    def createInstance(self):
        return BatchSummarizedExtractorAlgorithm()
