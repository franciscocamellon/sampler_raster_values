# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SamplerRasterValues
                                 A QGIS plugin
 Amostra valores de pixels a partir de rasters e preenche atributos de
 shapefiles no QGIS.
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
__date__ = '2023-10-27'
__copyright__ = '(C) 2023 by Francisco Camello'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.Qt import QVariant
from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterString,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer)

from .services.layer_services import LayerService


class SamplerRasterValuesAlgorithm(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    RASTER_INPUT = 'RASTER_INPUT'
    INPUT = 'INPUT'
    INPUT_FIELD = 'INPUT_FIELD'
    SELECTED = 'SELECTED'
    NEW_FIELD = 'NEW_FIELD'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER_INPUT,
                self.tr('Input raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Input point layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SELECTED, self.tr("Process only selected features")
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD,
                self.tr('Field for variable of interest'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.NEW_FIELD,
                self.tr('Create a field for variable of interest'),
                defaultValue='SAMPLE',
                optional=True
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT, self.tr("Original layer without empty geometries")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        layerService = LayerService()

        inputRasterLayer = self.parameterAsRasterLayer(parameters, self.RASTER_INPUT, context)
        inputPointLayer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        layerAttribute = self.parameterAsString(parameters, self.INPUT_FIELD, context)
        selectedOnly = self.parameterAsBool(parameters, self.SELECTED, context)
        newField = self.parameterAsString(parameters, self.NEW_FIELD, context)

        newFeatures = []

        if newField != 'SAMPLE':
            layerService.addNewField(inputPointLayer, newField, QVariant.Double)

        input_features = inputPointLayer.selectedFeatures() if selectedOnly else inputPointLayer.getFeatures()

        for feature in input_features:
            updated_feature = layerService.extractValueFromRaster(inputRasterLayer, feature,
                                                                  layerAttribute, newField)
            newFeatures.append(updated_feature)

        layerService.updateFeature(iface, inputPointLayer, newFeatures, feedback)

        return {self.OUTPUT: inputPointLayer}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Values Extractor'

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
        return SamplerRasterValuesAlgorithm()
