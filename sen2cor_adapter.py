# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Sen2CorAdapter
                                 A QGIS plugin
 Provides integration of the Sen2Cor tool in QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-03-25
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Mathis RACINNE-DIVET, IRISA, Université Bretagne Sud
        email                : mathracinne@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QXmlStreamWriter, QFile, QProcess
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QDialogButtonBox, QPushButton, QErrorMessage, QMessageBox, QProgressDialog
from qgis.gui import *
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .sen2cor_adapter_dialog import Sen2CorAdapterDialog

import os.path
import platform
import multiprocessing
import xml.etree.ElementTree as ET


class Sen2CorAdapter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Sen2CorAdapter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Sen2Cor Adapter')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Sen2CorAdapter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/sen2cor_adapter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sen2Cor Adapter'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&Sen2Cor Adapter'),
                action)
            self.iface.removeToolBarIcon(action)

    def writeGipp(self):
        """Creates a custom L2A_GIPP.xml file, using the values entered by the user in the GUI."""
        # Saving L2A-GIPP template and output path
        templateGippPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"L2A_GIPP_Template.xml")
        customGippPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"tmp","L2A_GIPP_Custom.xml")

        # Importing the template xml data
        tree = ET.parse(templateGippPath)
        root = tree.getroot()

        # Editing with user's custom settings
        if self.dlg.nbProcSpin.value() == 0:
            root.find("./Common_Section/Nr_Processes").text = "AUTO"
        else:
            root.find("./Common_Section/Nr_Processes").text = str(self.dlg.nbProcSpin.value())

        if self.dlg.outputChooser.filePath() == "":
            root.find("./Common_Section/Target_Directory").text = "DEFAULT"
        else:
            root.find("./Common_Section/Target_Directory").text = self.dlg.outputChooser.filePath()

        if self.dlg.demDirForm.text() == "":
            root.find("./Common_Section/DEM_Directory").text = "NONE"
        else:
            root.find("./Common_Section/DEM_Directory").text = self.dlg.demDirForm.text()

        root.find("./Common_Section/DEM_Reference").text = self.dlg.demRefForm.text()
        root.find("./Common_Section/Generate_DEM_Output").text = self.dlg.generateDemOutCombo.currentText()
        root.find("./Common_Section/Generate_TCI_Output").text = self.dlg.generateTciOutCombo.currentText()
        root.find("./Common_Section/Generate_DDV_Output").text = self.dlg.generateDdvOutCombo.currentText()
        root.find("./Scene_Classification/Filters/Median_Filter").text = str(self.dlg.medianFilterSpin.value())
        root.find("./Atmospheric_Correction/Look_Up_Tables/Aerosol_Type").text = self.dlg.aerosolCombo.currentText()
        root.find("./Atmospheric_Correction/Look_Up_Tables/Mid_Latitude").text = self.dlg.midLatCombo.currentText()
        root.find("./Atmospheric_Correction/Look_Up_Tables/Ozone_Content").text = self.dlg.ozoneCombo.currentText()
        root.find("./Atmospheric_Correction/Flags/WV_Correction").text = str(self.dlg.wvCorrectionSpin.value())
        root.find("./Atmospheric_Correction/Flags/VIS_Update_Mode").text = str(self.dlg.visUpdateSpin.value())
        root.find("./Atmospheric_Correction/Flags/WV_Watermask").text = str(self.dlg.wvWatermaskSpin.value())
        root.find("./Atmospheric_Correction/Flags/Cirrus_Correction").text = self.dlg.cirrusCorCombo.currentText()
        root.find("./Atmospheric_Correction/Flags/BRDF_Correction").text = self.dlg.brdfCorCombo.currentText()
        root.find("./Atmospheric_Correction/Flags/BRDF_Lower_Bound").text = self.dlg.brdfLowerForm.text()
        root.find("./Atmospheric_Correction/Calibration/DEM_Unit").text = str(self.dlg.demUnitSpin.value())
        root.find("./Atmospheric_Correction/Calibration/Adj_Km").text = self.dlg.adjacencyRangeForm.text()
        root.find("./Atmospheric_Correction/Calibration/Visibility").text = self.dlg.visibilityForm.text()
        root.find("./Atmospheric_Correction/Calibration/Altitude").text = self.dlg.altitudeForm.text()
        root.find("./Atmospheric_Correction/Calibration/Smooth_WV_Map").text = self.dlg.smoothWvMapForm.text()
        root.find("./Atmospheric_Correction/Calibration/WV_Threshold_Cirrus").text = self.dlg.wvThresCirrusForm.text()

        # Writing custom settings in new custom L2A_GIPP.xml file
        tree.write(customGippPath)


    def checkToolFolder(self):
        """Checks if the tool folder path specified by the user contains sen2cor executable.
            :returns: True if the folder contains sen2cor executable.
        """
        isOk = False
        if self.toolPath != "":
            if platform.system() == "Windows":
                self.toolProcessPath = os.path.join(self.toolPath,"L2A_Process.bat")
            else:
                self.toolProcessPath = os.path.join(self.toolPath,"bin","L2A_Process")

            if os.path.isfile(self.toolProcessPath):
                isOk = True
            else:
                msgBox = QMessageBox().warning(self.dlg, self.tr("Invalid SEN2COR folder"), self.tr("Invalid SEN2COR folder ! Ensure that you specified the SEN2COR tool folder (contains bin/ lib/ etc.) "))

        else:
            msgBox = QMessageBox().warning(self.dlg, self.tr("Missing SEN2COR path"), self.tr("Please specify the SEN2COR tool folder !"))

        return isOk

    def checkGippFile(self):
        """Checks if the L2A_GIPP file specified by the user exists.
            :returns: True if the file exists.
        """
        isOk = False
        if self.dlg.gippChooser.filePath() != "":
            if os.path.isfile(self.dlg.gippChooser.filePath()):
                isOk = True
            else:
                msgBox = QMessageBox().warning(self.dlg, self.tr("L2A_GIPP file not found"), self.tr("Unable to find specified L2A_GIPP file"))

        else:
            isOk = True

        return isOk


    def checkInput(self):
        """Checks if path inputs are valid, and if the parameters entered by the user are respecting the values specified in the SEN2COR documentation.
            :returns: True if all entered values are valid.
        """
        isOk = False

        if self.checkToolFolder():
            if self.checkGippFile():
                if self.dlg.inputChooser.filePath() != "":
                    if self.checkBrdfBounds():
                        if self.checkVisibilityBounds():
                            if self.checkAltitudeBounds():
                                if self.checkWvThresBounds():
                                    if self.checkAdjacencyBounds():
                                        if self.checkSmoothWvMapBounds():
                                            self.writeGipp()
                                            isOk = True
                                        else:
                                            msgBox = QMessageBox().warning(self.dlg, self.tr("Bad parameter value"), self.tr("SmoothWV map value must be between 0.0 and 300 !"))
                                    else:
                                        msgBox = QMessageBox().warning(self.dlg, self.tr("Bad parameter value"), self.tr("Adjacency range value must be between 0.0 and 10 !"))
                                else:
                                    msgBox = QMessageBox().warning(self.dlg, self.tr("Bad parameter value"), self.tr("Wv thres cirrus value must be between 0.1 and 1.0 !"))
                            else:
                                msgBox = QMessageBox().warning(self.dlg, self.tr("Bad parameter value"), self.tr("Altitude value must be between 0 and 2.5 !"))
                        else:
                            msgBox = QMessageBox().warning(self.dlg, self.tr("Bad parameter value"), self.tr("Visibility value must be between 5 and 120 !"))
                    else:
                        msgBox = QMessageBox().warning(self.dlg, self.tr("Bad parameter value"), self.tr("Brdf lower bound value must be between 0.1 and 0.25 !"))
                else:
                    msgBox = QMessageBox().warning(self.dlg, self.tr("Missing input"), self.tr("Please select a .SAFE input folder !"))

        return isOk


    def checkBrdfBounds(self):
        """Checks if the brdf lower bound value entered by the user is valid.
            :returns: True if the value is valid.
        """
        isOk = True
        minBound = 0.1
        maxBound = 0.25
        try:
            value = float(self.dlg.brdfLowerForm.text())
            if (minBound > value) or (maxBound < value):
                isOk = False

        except (ValueError, TypeError):
            isOk = False

        return isOk


    def checkVisibilityBounds(self):
        """Checks if the visibility value entered by the user is valid.
            :returns: True if the value is valid.
        """
        isOk = True
        minBound = 5.0
        maxBound = 120.0
        try:
            value = float(self.dlg.visibilityForm.text())
            if (minBound > value) or (maxBound < value):
                isOk = False

        except (ValueError, TypeError):
            isOk = False

        return isOk


    def checkAltitudeBounds(self):
        """Checks if the altitude value entered by the user is valid.
            :returns: True if the value is valid.
        """
        isOk = True
        minBound = 0.0
        maxBound = 2.5
        try:
            value = float(self.dlg.altitudeForm.text())
            if (minBound > value) or (maxBound < value):
                isOk = False

        except (ValueError, TypeError):
            isOk = False

        return isOk


    def checkWvThresBounds(self):
        """Checks if the WV_Threshold_Cirrus value entered by the user is valid.
            :returns: True if the value is valid.
        """
        isOk = True
        minBound = 0.1
        maxBound = 1.0
        try:
            value = float(self.dlg.wvThresCirrusForm.text())
            if (minBound > value) or (maxBound < value):
                isOk = False

        except (ValueError, TypeError):
            isOk = False

        return isOk

    def checkAdjacencyBounds(self):
        """Checks if the adjacency range value entered by the user is valid.
            :returns: True if the value is valid.
        """
        isOk = True
        minBound = 0.0
        maxBound = 10.0
        try:
            value = float(self.dlg.adjacencyRangeForm.text())
            if (minBound > value) or (maxBound < value):
                isOk = False

        except (ValueError, TypeError):
            isOk = False

        return isOk

    def checkSmoothWvMapBounds(self):
        """Checks if the smoothWvMap value entered by the user is valid.
            :returns: True if the value is valid.
        """
        isOk = True
        minBound = 0.0
        maxBound = 300.0
        try:
            value = float(self.dlg.smoothWvMapForm.text())
            if (minBound > value) or (maxBound < value):
                isOk = False

        except (ValueError, TypeError):
            isOk = False

        return isOk

    def logProcessOutput(self):
        """Displays sen2cor process output in the log text area."""
        cursor = self.dlg.consoleArea.textCursor()
        cursor.movePosition(cursor.End)
        outText = str(self.process.readAllStandardOutput(), encoding='utf-8')
        cursor.insertText(outText)
        cursor.insertText(str(self.process.readAllStandardError(), encoding='utf-8'))
        self.dlg.consoleArea.ensureCursorVisible()
        # Parses progress value from sen2cor logs, to set the progress bar value
        if outText[slice(12)] == "Progress[%]:":
            #Checks if the progress bar was in undetermined state (range of (0,0))
            if self.dlg.progressBar.maximum() != 100:
                self.dlg.progressBar.setRange(0,100)

            #If progress value is x.xx
            if outText[14] == '.':
                try:
                    # retrieve integer part of the float progress value (first digit)
                    value = int(outText[13])
                    self.dlg.progressBar.setValue(value)
                    self.previousValue = value
                except (ValueError, TypeError):
                    self.dlg.progressBar.setValue(self.previousValue)
            # else it is xx.xx
            else:
                try:
                    # retrieve integer part of the float progress value (2 first digits)
                    value = int(outText[slice(13,15,1)])
                    self.dlg.progressBar.setValue(value)
                    self.previousValue = value
                except (ValueError, TypeError):
                    self.dlg.progressBar.setValue(self.previousValue)
        # If the line is not in the form of "Progress[%]: x", sets the progress bar to undetermined state
        else:
            self.dlg.progressBar.setRange(0,0)

    def disableRunButton(self):
        """Called when sen2cor processing starts. Disables run button, enables stop button and shows the log text area."""
        self.dlg.runButton.setEnabled(False)
        self.dlg.stopButton.setEnabled(True)
        self.dlg.scrollArea.setEnabled(False)
        # Displays the log tab
        self.dlg.tabWidget.setCurrentIndex(1)
        #Sets progress bar to undetermined state
        self.dlg.progressBar.setRange(0,0)
        self.dlg.progressBar.setValue(0)
        self.previousValue = 0

    def enableRunButton(self):
        """Called when sen2cor processing ends. Disables stop button and enables stop button. Performs importation in QGIS project if wanted."""
        self.dlg.runButton.setEnabled(True)
        self.dlg.stopButton.setEnabled(False)
        self.dlg.scrollArea.setEnabled(True)
        # Sets the progress bar as finished
        self.dlg.progressBar.setRange(0,100)
        self.dlg.progressBar.setValue(100)
        # If the process finished by itself (not a user stop action)
        if self.process.exitCode() == 0 and not self.dlg.crCheck.isChecked():
            # Asking if the user wants to import the processed product
            result = QMessageBox().question(self.dlg, self.tr("Import processed product ?"), self.tr("Process finished !\nDo you want to import the processed product into your QGIS project ?\n\nNOTE: Depending on your product size, QGIS and Sen2Cor_Adapter windows may freeze for a couple of seconds during importation."), QMessageBox.Yes, QMessageBox.No)
            if result == QMessageBox.Yes:
                importSuccess = False
                # If the output dir was specified
                if self.dlg.outputChooser.filePath() != "":
                    outputProduct = os.path.join(self.dlg.outputChooser.filePath(),os.path.basename(self.dlg.inputChooser.filePath().replace('L1C','L2A')))
                # Otherwise we use the default output (same parent folder than input product)
                else:
                    outputProduct = self.dlg.inputChooser.filePath().replace('L1C','L2A')
                # Then checking if the product has a valid structure
                if os.path.isdir(outputProduct):
                    imagesPath = os.path.join(outputProduct,"GRANULE")
                    if os.path.isdir(imagesPath):
                        L2AFolder = os.listdir(imagesPath)[0]
                        if L2AFolder[slice(3)] == "L2A":
                            imagesPath = os.path.join(imagesPath,L2AFolder)
                            if os.path.isdir(imagesPath):
                                imagesPath = os.path.join(imagesPath,"IMG_DATA")
                                if os.path.isdir(imagesPath):
                                    resolutions = os.listdir(imagesPath)
                                    # Retrieving root node of the tree layer in QGIS project
                                    layersRoot = QgsProject.instance().layerTreeRoot()
                                    # Adding subgroup containing all the processed product to import
                                    productGroup = layersRoot.addGroup(L2AFolder)
                                    productGroup.setItemVisibilityChecked(False)
                                    productGroup.setExpanded(False)
                                    importSuccess = True
                                    # For each resolution, i.e 60, 20 and/or 10m
                                    for resFolder in resolutions:
                                        # Creating a subgroup containing all files of the same resolution
                                        resolutionGroup = productGroup.addGroup(resFolder)
                                        resolutionGroup.setItemVisibilityChecked(False)
                                        resolutionGroup.setExpanded(False)
                                        rasterFolder = os.path.join(imagesPath,resFolder)
                                        # For each raster file of the current resolution
                                        for rasterFile in os.listdir(rasterFolder):
                                            # Importing the raster file as a raster layer, naming it with its related band name.
                                            # (The band name is specified at the end of the file name, that we extract using slice() method)
                                            rasterLayer = QgsRasterLayer(os.path.join(rasterFolder,rasterFile),rasterFile[slice(int(len(rasterFile)-11),int(len(rasterFile)-4),1)])
                                            if rasterLayer.isValid():
                                                # Adding the raster layer to the project, without placing it in the layer tree.
                                                QgsProject.instance().addMapLayer(rasterLayer, False)
                                                # Insert the raster layer in the layer tree, in the related resolution group.
                                                insertedLayer = resolutionGroup.insertLayer(-1, rasterLayer)
                                                insertedLayer.setItemVisibilityChecked(False)
                                                insertedLayer.setExpanded(False)
                if importSuccess:
                    QMessageBox().information(self.dlg,self.tr("Import result"),self.tr("Import successful !"))
                else:
                    QMessageBox().critical(self.dlg,self.tr("Import result"),self.tr("Import failed !\nDid you changed the output product structure or name ?"))

    def stopProcess(self):
        """Called by pressing stop button. Kills sen2cor running process."""
        # Asking for confirmation
        result = QMessageBox().question(self.dlg, self.tr("Stop process ?"), self.tr("Are you sure that you want to stop SEN2COR process ?"), QMessageBox.Yes, QMessageBox.No)
        if result == QMessageBox.Yes:
            if platform.system() == "Windows":
                # If we are on Windows, there is a way to kill all subprocesses in one command (using /T param)
                QProcess.execute("cmd",["/c","taskkill","/PID",str(self.process.processId()),"/T","/F"])
            else:
                # If we are on Linux, we have to retrieve all subprocesses PIDs, so as to kill them.
                # Because SEN2COR creates its own child processes, we don't know their PIDs without retrieving them using ps command.
                childIds = []
                getChild = QProcess()
                parentPid = str(self.process.processId())
                getChild.start("ps",["--ppid",parentPid,"-o","pid","--no-heading"])
                getChild.waitForFinished(5000)
                lastChildFound = str(getChild.readAllStandardOutput(), encoding='utf-8')
                lastChildFound = lastChildFound.replace('\n','')
                lastChildFound = lastChildFound.replace(' ','')

                if len(lastChildFound) >= 1:
                    # Iterate until the last child process found hasn't any subprocess
                    while len(lastChildFound) >= 1:
                        childIds.append(lastChildFound)
                        getChild.start("ps",["--ppid",lastChildFound,"-o","pid","--no-heading"])
                        getChild.waitForFinished(5000)
                        lastChildFound = str(getChild.readAllStandardOutput(), encoding='utf-8')
                        lastChildFound = lastChildFound.replace('\n','')
                        lastChildFound = lastChildFound.replace(' ','')
                    QProcess.execute("kill",childIds)
                else:
                    self.process.terminate()

    def runProcess(self):
        """Starts the SEN2COR processing, by calling SEN2COR executable in a subprocess, with the required params (i.e resolution or L2A_GIPP.xml file path)."""
        # Displays start message in log area
        cursor = self.dlg.consoleArea.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText("Starting SEN2COR process, please wait...\n")

        # String array, in which all command params will be stored.
        commandParams = []

        if platform.system() == "Windows":
            command = "cmd"
            commandParams.append("/c")
            script = os.path.join(self.toolPath,"L2A_Process.bat")
        else:
            command = "bash"
            script = os.path.join(self.toolPath,"bin","L2A_Process")

        # Adds sen2cor executable as param
        commandParams.append(script)

        # Adds resolution value as param
        # If ALL is choosen, no resolution param is given (All resolutions are processed by default in sen2cor)
        resText = str(self.dlg.resCombo.currentText())
        if resText != "ALL":
            commandParams.append("--resolution")
            commandParams.append(resText)

        if self.dlg.scCheck.isChecked():
            commandParams.append("--sc_only")

        if self.dlg.crCheck.isChecked():
            commandParams.append("--cr_only")

        # Adds L2A_GIPP.xml file as param
        commandParams.append("--GIP_L2A")
        # If no L2A_GIPP.xml file is specified by the user, uses the automatically generated one with the parameters entered in the form.
        if self.dlg.gippChooser.filePath() == "":
            if platform.system() == "Windows":
                gippL2APath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"tmp","L2A_GIPP_Custom.xml")
            else:
                gippL2APath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"tmp","L2A_GIPP_Custom.xml")

            commandParams.append(gippL2APath)
        # Otherwise, gives the L2A_GIPP.xml file specified by the user directly to sen2cor.
        else:
            gippL2APath = self.dlg.gippChooser.filePath()
            commandParams.append(gippL2APath)

        # Last param is the .SAFE folder path, which is the Sentinel-2 product to be processed.
        commandParams.append(self.dlg.inputChooser.filePath())

        # Finally, starts the process with the command (cmd or bash) and its params stored in the commandParams array.
        # It calls the sen2cor executable given in params using cmd or bash.
        self.process.start(command,commandParams)

    def startProcess(self):
        """Called when start button is pressed. Checks if all user inputs are valid, then starts the sen2cor process."""
        if self.checkInput():
            self.runProcess()

    def saveToolPath(self):
        """Stores the last sen2cor tool path entered by the user in a temporary file."""
        tmpFile = open(self.tmpToolPath, "w")
        self.toolPath = self.dlg.toolPathChooser.filePath()
        tmpFile.write(self.toolPath)
        tmpFile.close()

    def showLicense(self):
        self.dlg.licenseButton.setEnabled(False)
        # Fill about tab text area with LICENSE file text
        licenseFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"LICENSE")
        if os.path.isfile(licenseFilePath):
            licenseFile = open(licenseFilePath, "r")
            cursor = self.dlg.aboutTextArea.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText("\n####################################\nLICENSE\n####################################\n")
            cursor.insertText(licenseFile.read())
            licenseFile.close()

    def toggleCustomSettings(self):
        """Enables the user to custom sen2cor settings if no LA2_GIPP file has been entered.
            Otherwise, it disables the input form if a L2A_GIPP file has been entered."""
        if self.dlg.gippChooser.filePath() == "":
            # Enables every custom settings.
            self.dlg.nbProcSpin.setEnabled(True)
            self.dlg.medianFilterSpin.setEnabled(True)
            self.dlg.aerosolCombo.setEnabled(True)
            self.dlg.midLatCombo.setEnabled(True)
            self.dlg.ozoneCombo.setEnabled(True)
            self.dlg.wvCorrectionSpin.setEnabled(True)
            self.dlg.visUpdateSpin.setEnabled(True)
            self.dlg.wvWatermaskSpin.setEnabled(True)
            self.dlg.cirrusCorCombo.setEnabled(True)
            self.dlg.brdfCorCombo.setEnabled(True)
            self.dlg.brdfLowerForm.setEnabled(True)
            self.dlg.visibilityForm.setEnabled(True)
            self.dlg.altitudeForm.setEnabled(True)
            self.dlg.wvThresCirrusForm.setEnabled(True)
            self.dlg.demDirForm.setEnabled(True)
            self.dlg.demRefForm.setEnabled(True)
            self.dlg.demUnitSpin.setEnabled(True)
            self.dlg.adjacencyRangeForm.setEnabled(True)
            self.dlg.smoothWvMapForm.setEnabled(True)
            self.dlg.generateDemOutCombo.setEnabled(True)
            self.dlg.generateTciOutCombo.setEnabled(True)
            self.dlg.generateDdvOutCombo.setEnabled(True)
        else:
            # Disables every custom settings.
            self.dlg.nbProcSpin.setEnabled(False)
            self.dlg.medianFilterSpin.setEnabled(False)
            self.dlg.aerosolCombo.setEnabled(False)
            self.dlg.midLatCombo.setEnabled(False)
            self.dlg.ozoneCombo.setEnabled(False)
            self.dlg.wvCorrectionSpin.setEnabled(False)
            self.dlg.visUpdateSpin.setEnabled(False)
            self.dlg.wvWatermaskSpin.setEnabled(False)
            self.dlg.cirrusCorCombo.setEnabled(False)
            self.dlg.brdfCorCombo.setEnabled(False)
            self.dlg.brdfLowerForm.setEnabled(False)
            self.dlg.visibilityForm.setEnabled(False)
            self.dlg.altitudeForm.setEnabled(False)
            self.dlg.wvThresCirrusForm.setEnabled(False)
            self.dlg.demDirForm.setEnabled(False)
            self.dlg.demRefForm.setEnabled(False)
            self.dlg.demUnitSpin.setEnabled(False)
            self.dlg.adjacencyRangeForm.setEnabled(False)
            self.dlg.smoothWvMapForm.setEnabled(False)
            self.dlg.generateDemOutCombo.setEnabled(False)
            self.dlg.generateTciOutCombo.setEnabled(False)
            self.dlg.generateDdvOutCombo.setEnabled(False)


    def run(self):
        """Run method called each time the plugin is opened in QGIS."""

        # Builds the GUI and its components, if it is the first time the plugin is launched.
        if self.first_start == True:
            self.first_start = False
            #Saves the temporary file path, which contains last sen2cor path entered by the user.
            self.tmpToolPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"tmp","lastToolPath.tmp")
            # Creates and saves the plugin dialog window instance.
            self.dlg = Sen2CorAdapterDialog()
            self.dlg.tabWidget.setCurrentIndex(0)
            self.dlg.consoleArea.setReadOnly(True)

            # Add run and stop buttons in bottom button box
            self.dlg.runButton = QPushButton("Run")
            self.dlg.stopButton = QPushButton("Stop")
            self.dlg.stopButton.setEnabled(False)
            self.dlg.button_box.addButton(self.dlg.runButton, QDialogButtonBox.ActionRole)
            self.dlg.button_box.addButton(self.dlg.stopButton, QDialogButtonBox.ActionRole)
            self.dlg.runButton.clicked.connect(self.startProcess)
            self.dlg.stopButton.clicked.connect(self.stopProcess)
            self.dlg.licenseButton.clicked.connect(self.showLicense)

            # Config sen2cor tool path chooser to ask for a directory
            self.dlg.toolPathChooser.setStorageMode(self.dlg.toolPathChooser.StorageMode.GetDirectory)
            self.dlg.toolPathChooser.fileChanged.connect(self.saveToolPath)
            # Config input file chooser to ask for a directory
            self.dlg.inputChooser.setStorageMode(self.dlg.inputChooser.StorageMode.GetDirectory)
            self.dlg.outputChooser.setStorageMode(self.dlg.outputChooser.StorageMode.GetDirectory)
            # Set max number of processes
            self.dlg.nbProcSpin.setMaximum(multiprocessing.cpu_count())
            # init resolution combo
            self.dlg.resCombo.addItems(["10","20","60","ALL"])
            # same for L2A_GIPP file chooser
            self.dlg.gippChooser.fileChanged.connect(self.toggleCustomSettings)
            # Config L2A_GIPP file chooser to ask for a file
            self.dlg.gippChooser.setStorageMode(self.dlg.gippChooser.StorageMode.GetFile)
            # Adding values for each combo
            self.dlg.aerosolCombo.addItems(["RURAL","MARITIME"])
            self.dlg.midLatCombo.addItems(["SUMMER","WINTER"])
            self.dlg.ozoneCombo.addItems(["0","250","290","330","331","370","377","410","420","450","460"])
            self.dlg.cirrusCorCombo.addItems(["TRUE","FALSE"])
            self.dlg.brdfCorCombo.addItems(["0","1","2","11","12","22","21"])
            self.dlg.generateDemOutCombo.addItems(["TRUE","FALSE"])
            self.dlg.generateTciOutCombo.addItems(["TRUE","FALSE"])
            self.dlg.generateDdvOutCombo.addItems(["TRUE","FALSE"])
            # QProcess object for external app
            self.process = QProcess()
            # QProcess emits `readyRead` when there is data to be read
            self.process.readyRead.connect(self.logProcessOutput)
            self.process.started.connect(self.disableRunButton)
            self.process.finished.connect(self.enableRunButton)
            # Sets the progress bar value to 0
            self.dlg.progressBar.setRange(0,100)
            self.dlg.progressBar.setValue(0)


        # Checking if sen2cor path has already been entered by the user.
        # If yes, reads the path saved in temporary file, and stores it in the related form.
        if os.path.isfile(self.tmpToolPath):
            tmpFile = open(self.tmpToolPath, "r")
            self.dlg.toolPathChooser.setFilePath(tmpFile.readline())
            tmpFile.close()

        # Initializing default values
        self.dlg.scCheck.setChecked(False)
        self.dlg.crCheck.setChecked(False)
        self.dlg.resCombo.setCurrentIndex(2)
        self.dlg.aerosolCombo.setCurrentIndex(0)
        self.dlg.midLatCombo.setCurrentIndex(0)
        self.dlg.ozoneCombo.setCurrentIndex(0)
        self.dlg.cirrusCorCombo.setCurrentIndex(1)
        self.dlg.brdfCorCombo.setCurrentIndex(0)
        self.dlg.generateDemOutCombo.setCurrentIndex(1)
        self.dlg.generateTciOutCombo.setCurrentIndex(0)
        self.dlg.generateDdvOutCombo.setCurrentIndex(1)
        self.dlg.brdfLowerForm.setText(str("0.22"))
        self.dlg.visibilityForm.setText(str("40.0"))
        self.dlg.altitudeForm.setText(str("0.100"))
        self.dlg.wvThresCirrusForm.setText(str("0.25"))
        self.dlg.adjacencyRangeForm.setText(str("1.0"))
        self.dlg.smoothWvMapForm.setText(str("100.0"))

        # shows the dialog windows
        self.dlg.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
        #    pass
