# -*- coding: utf-8 -*-

"""
/***************************************************************************
 LayerService
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
__date__ = '2023-10-27'
__copyright__ = '(C) 2023 by CamellOnCase'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import numpy as np

from osgeo import gdal
from qgis.core.additions.edit import edit
from qgis.core import QgsProject, QgsFeature, QgsField, QgsFields, QgsPointXY, QgsVectorLayer, QgsRasterLayer, QgsRasterDataProvider
from qgis.PyQt.Qt import QVariant

from .system_service import SystemService

STATISTICS_DICTIONARY = {
    'STATISTICS_MINIMUM': 0.0,
    'STATISTICS_MAXIMUM': 0.0,
    'STATISTICS_MEAN': 0.0,
    'STATISTICS_MEDIAN': 0.0,
    'STATISTICS_STDDEV': 0.0
}


class LayerService:

    def __init__(self):
        """
        Constructor for the LayerService class.
        """
        self.systemService = SystemService()

    @staticmethod
    def isEditable(layer):
        return layer.isEditable()

    @staticmethod
    def addNewField(layer, fieldName, fieldType):
        """
        Adds a new field to a QGIS vector layer.
        :param layer: The vector layer to which the field is added.
        :param fieldName: The name of the new field.
        :param fieldType: The data type of the new field.
        """
        with edit(layer):
            layer.addAttribute(QgsField(fieldName, fieldType))
            layer.updateFields()

    def createFields(self, fieldDictionary):
        layerFields = QgsFields()

        for fieldName, fieldType in fieldDictionary.items():
            layerField = QgsField(fieldName, self.dtypeToVariant(fieldType))
            layerFields.append(layerField)

        return layerFields

    def createField(self):
        pass

    @staticmethod
    def dtypeToVariant(fieldType):
        if fieldType == 'int64':
            return QVariant.Int
        elif fieldType == '<M8[ns]':
            return QVariant.String
        elif fieldType == 'float64':
            return QVariant.Double
        else:
            return QVariant.String

    @staticmethod
    def extractValueFromRaster(raster, feature, fieldName, newFieldName):
        """
        Extracts a value from a raster at the location of a feature's geometry point.
        :param raster: The raster layer from which to extract the value.
        :param feature: The feature for which the value is extracted.
        :param fieldName: The name of the field where the extracted value will be stored.
        :param newFieldName: The name of the new field (if not 'SAMPLE').
        :returns: The updated feature with the extracted value.
        """
        geometry = feature.geometry()
        observation_point = geometry.asPoint()
        x, y = observation_point.x(), observation_point.y()

        pixel_value, success = raster.dataProvider().sample(QgsPointXY(x, y), 1)

        if success:
            if newFieldName != 'SAMPLE':
                feature[newFieldName] = pixel_value
            else:
                feature[fieldName] = pixel_value

        return feature

    @staticmethod
    def updateFeature(iface, layer, featureList, feedback):
        """
        Updates a list of features in a vector layer.
        :param iface: instance of QgsInterface.
        :param layer: The vector layer containing the features to be updated.
        :param featureList: List of features to update.
        :param feedback: Feedback object for progress and user cancellation.
        """
        iface.setActiveLayer(layer)
        layer.startEditing()
        layer.beginEditCommand('Adding new feature')

        totalFeatures = len(featureList)
        progressPerFeature = 100.0 / totalFeatures if totalFeatures else 0

        for featureIndex, feature in enumerate(featureList):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            try:
                # Update a feature in the layer
                layer.updateFeature(feature)
            except Exception as e:
                pass

            # Update the progress bar
            feedback.setProgress(int(featureIndex * progressPerFeature))

        layer.triggerRepaint()
        layer.endEditCommand()

    def createNetcdfRaster(self, netcdfInt, rasterName, rasterUri, gdalRaster=False):
        """
        Creates a QGIS raster layer from a NetCDF dataset.
        :param netcdfInt: NetCDF variable integer identifier (0 or 1).
        :param rasterName: Name of the new raster layer.
        :param rasterUri: URI of the NetCDF file.
        :param gdalRaster: Boolean to control flow.
        :returns: The created QGIS raster layer.
        """
        netcdfVariable = self.retrieveNetcdfVariable(netcdfInt)
        uri = f'NETCDF:"{rasterUri}":{netcdfVariable}'

        if gdalRaster:
            return gdal.Open(uri)

        return QgsRasterLayer(uri, rasterName)

    @staticmethod
    def createQgsRasterLayer(rasterUri, rasterName):
        return QgsRasterLayer(rasterUri, rasterName, "gdal")

    @staticmethod
    def retrieveNetcdfVariable(netcdfVariable):
        """
        Retrieves the NetCDF variable name based on an integer identifier.
        :param netcdfVariable: Integer identifier (0 or 1).
        :returns: The corresponding NetCDF variable name ('chlor_a' or 'sst').
        """
        if netcdfVariable == 0:
            return 'chlor_a'
        else:
            return 'sst'

    @staticmethod
    def getDateFromFeature(feature, dateField):
        """
        Retrieves a date value from a feature's field.
        :param feature: The feature containing the date field.
        :param dateField: The name of the date field.
        :returns: The date as a Python datetime object.
        """
        data_field = feature[dateField]
        return data_field.toPyDate()

    def checkFeatureDateRange(self, feature, imageFile, dateField):

        startDate, endDate = self.systemService.getDateRange(imageFile)
        dateObject = self.getDateFromFeature(feature, dateField)

        return self.systemService.isDateWithinRange(dateObject, startDate, endDate)

    @staticmethod
    def readGdalRasterAsArray(gdalRaster, bandNumber):
        rasterBand = gdalRaster.GetRasterBand(bandNumber)
        return rasterBand.ReadAsArray()

    @staticmethod
    def getGdalMetadata(gdalRasterBand):
        return gdalRasterBand.GetMetadata()

    def getSummaryStatistics(self, rasterLayer, bandNumber, aquaModisVariable=None):
        band = rasterLayer.GetRasterBand(bandNumber)
        band.ComputeStatistics(0)
        metadata = self.getGdalMetadata(band)
        bandAsArray = band.ReadAsArray()

        if aquaModisVariable == 'chlor_a':
            mask = bandAsArray != int(metadata['_FillValue'])
            chlorArray = bandAsArray[mask]

            STATISTICS_DICTIONARY['STATISTICS_MINIMUM'] = float(metadata['STATISTICS_MINIMUM'])
            STATISTICS_DICTIONARY['STATISTICS_MAXIMUM'] = float(metadata['STATISTICS_MAXIMUM'])
            STATISTICS_DICTIONARY['STATISTICS_MEAN'] = float(metadata['STATISTICS_MEAN'])
            STATISTICS_DICTIONARY['STATISTICS_MEDIAN'] = float(np.median(chlorArray))
            STATISTICS_DICTIONARY['STATISTICS_STDDEV'] = float(metadata['STATISTICS_STDDEV'])

            return STATISTICS_DICTIONARY

        if 'scale_factor' in metadata and float(metadata['scale_factor']) < 1:
            mask = bandAsArray != int(metadata['_FillValue'])
            sttArray = bandAsArray[mask]

            STATISTICS_DICTIONARY['STATISTICS_MINIMUM'] = float(metadata['STATISTICS_MINIMUM']) * float(
                metadata['scale_factor'])
            STATISTICS_DICTIONARY['STATISTICS_MAXIMUM'] = float(metadata['STATISTICS_MAXIMUM']) * float(
                metadata['scale_factor'])
            STATISTICS_DICTIONARY['STATISTICS_MEAN'] = float(metadata['STATISTICS_MEAN']) * float(
                metadata['scale_factor'])
            STATISTICS_DICTIONARY['STATISTICS_MEDIAN'] = float(np.median(sttArray)) * float(metadata['scale_factor'])
            STATISTICS_DICTIONARY['STATISTICS_STDDEV'] = float(metadata['STATISTICS_STDDEV']) * float(
                metadata['scale_factor'])

            return STATISTICS_DICTIONARY

    @staticmethod
    def createFeature(fields, param):
        feature = QgsFeature(fields)
        feature['id'] = param[0]
        feature['Observation date'] = str(param[1])
        feature['Start date'] = str(param[2])
        feature['End date'] = str(param[3])
        feature['Variable'] = param[4]
        feature['Minimum'] = param[5]['STATISTICS_MINIMUM']
        feature['Maximum'] = param[5]['STATISTICS_MAXIMUM']
        feature['Median'] = param[5]['STATISTICS_MEAN']
        feature['Mean'] = param[5]['STATISTICS_MEDIAN']
        feature['Stddev'] = param[5]['STATISTICS_STDDEV']

        return feature

    @staticmethod
    def loadNonSpatialLayer(layerPath, layerName):
        nonSpatialLayer = QgsVectorLayer(layerPath, layerName, 'ogr')
        if nonSpatialLayer.isValid():
            QgsProject.instance().addMapLayer(nonSpatialLayer)
