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
        copyright            : (C) 2019 by Mathis RACINNE-DIVET
        email                : mathracinne@gmail.com
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QXmlStreamWriter
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QDialogButtonBox, QPushButton, QErrorMessage, QMessageBox
from qgis.gui import *
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .sen2cor_adapter_dialog import Sen2CorAdapterDialog

import os.path
import multiprocessing


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


    def toggleCustomSettings(self):
        """Enables the user to custom sen2cor settings if no LA2_GIPP file has been entered"""
        if self.dlg.gippChooser.filePath() == "":
            # Enable every custom settings
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
            # Disable every custom settings
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

    def debugLog(self, message):
        self.dlg.paramsLab.setText(message)

    def checkInput(self):
        isOk = False

        if self.dlg.inputChooser.filePath() != "":
            if self.checkBrdfBounds():
                if self.checkVisibilityBounds():
                    if self.checkAltitudeBounds():
                        if self.checkWvThresBounds():
                            if self.checkAdjacencyBounds():
                                if self.checkSmoothWvMapBounds():
                                    pass
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


    def startProcess(self):
        self.checkInput()

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = Sen2CorAdapterDialog()
            # Add run button in bottom button box
            self.dlg.runButton = QPushButton("Run")
            self.dlg.button_box.addButton(self.dlg.runButton, QDialogButtonBox.ActionRole)
            self.dlg.runButton.clicked.connect(self.startProcess)
            # Config input file chooser to ask for a directory
            self.dlg.inputChooser.setStorageMode(self.dlg.inputChooser.StorageMode.GetDirectory)
            self.dlg.outputChooser.setStorageMode(self.dlg.outputChooser.StorageMode.GetDirectory)
            # Set max number of processes
            self.dlg.nbProcSpin.setMaximum(multiprocessing.cpu_count())
            # init resolution combo
            self.dlg.resCombo.addItems(["10","20","60","ALL"])
            self.dlg.resCombo.setCurrentIndex(2)
            # same for L2A_GIPP file chooser
            self.dlg.gippChooser.fileChanged.connect(self.toggleCustomSettings)
            # Config L2A_GIPP file chooser to ask for a file
            self.dlg.gippChooser.setStorageMode(self.dlg.gippChooser.StorageMode.GetFile)
            # Adding values for each combo
            self.dlg.aerosolCombo.addItems(["RURAL","MARITIME","AUTO"])
            self.dlg.aerosolCombo.setCurrentIndex(2)
            self.dlg.midLatCombo.addItems(["SUMMER","WINTER","AUTO"])
            self.dlg.midLatCombo.setCurrentIndex(2)
            self.dlg.ozoneCombo.addItems(["0","250","290","330","331","370","377","410","420","450","460"])
            self.dlg.ozoneCombo.setCurrentIndex(0)
            self.dlg.cirrusCorCombo.addItems(["TRUE","FALSE"])
            self.dlg.cirrusCorCombo.setCurrentIndex(1)
            self.dlg.brdfCorCombo.addItems(["0","1","2","11","12","22","21"])
            self.dlg.brdfCorCombo.setCurrentIndex(0)
            self.dlg.generateDemOutCombo.addItems(["TRUE","FALSE"])
            self.dlg.generateDemOutCombo.setCurrentIndex(1)
            self.dlg.generateTciOutCombo.addItems(["TRUE","FALSE"])
            self.dlg.generateTciOutCombo.setCurrentIndex(0)
            self.dlg.generateDdvOutCombo.addItems(["TRUE","FALSE"])
            self.dlg.generateDdvOutCombo.setCurrentIndex(1)


        #MAIN CODE



        #END MAIN CODE


        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
        #    pass
