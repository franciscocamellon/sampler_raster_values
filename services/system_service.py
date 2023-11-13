# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SystemService
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

import os
import csv
import numpy as np

from datetime import datetime
from qgis.core.additions.edit import edit
from qgis.core import QgsField, QgsPointXY, QgsRasterLayer


class SystemService:

    def __init__(self):
        """
        Constructor for the SystemService class.
        """
        pass

    def readFilePoints(self, filePath):
        with open('example.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                print(', '.join(row))

    @staticmethod
    def getDictHeaderTypes(dataFrame):
        dataFrameDictionary = dict()
        for columnName, columnType in dataFrame.dtypes.to_dict().items():
            dataFrameDictionary[columnName] = columnType
        return dataFrameDictionary

    def getDateRange(self, fileName, rangeType=False):
        """
        Extracts a date range from a filename and returns it as a tuple of start and end dates.
        :param fileName: The name of the file containing the date range information.
        :param rangeType: Boolean to control flow.
        :returns: A tuple (startDate, endDate) as datetime.date objects.
        """
        parts = self.splitString(fileName, '.')
        dateRangeStr = parts[1]

        if rangeType:
            return dateRangeStr

        startDateStr, endDateStr = self.splitString(dateRangeStr, '_')

        startDate = self.formatDate(startDateStr)
        endDate = self.formatDate(endDateStr)
        return startDate, endDate

    @staticmethod
    def isDateWithinRange(date, startDate, endDate):
        """
        Check if a date is within a specified date range.
        :param date: The date to check.
        :param startDate: The start date of the range.
        :param endDate: The end date of the range.
        :returns: True if the date is within the range, False otherwise.
        """
        return startDate <= date <= endDate

    @staticmethod
    def formatDate(stringDate):
        """
        Converts a string date in the format 'YYYYMMDD' to a datetime.date object.
        :param stringDate: The string date to format.
        :returns: A datetime.date object.
        """
        return datetime.strptime(stringDate, "%Y-%m-%d").date()

    @staticmethod
    def splitString(string, character):
        """
        Splits a string using a specified character and returns a list of substrings.
        :param string: The string to split.
        :param character: The character to use as a delimiter.
        :returns: A list of substrings.
        """
        return string.split(character)

    @staticmethod
    def filterFilesInDirectory(directory, fileType):
        filesInDirectory = []
        for current, imageFile in enumerate(os.listdir(directory)):
            if imageFile.lower().endswith(fileType) and os.path.isfile(os.path.join(directory, imageFile)):
                filesInDirectory.append(os.path.join(directory, imageFile))

        return filesInDirectory


