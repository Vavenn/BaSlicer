# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt, QSettings, QEvent)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QLabel, QLayout,
    QMainWindow, QRadioButton, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)
import pyaudio

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        if not SettingsWindow.objectName():
            SettingsWindow.setObjectName(u"SettingsWindow")
        SettingsWindow.resize(652, 446)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(SettingsWindow.sizePolicy().hasHeightForWidth())
        SettingsWindow.setSizePolicy(sizePolicy)
        self.settingscentralwidget = QWidget(SettingsWindow)
        self.settingscentralwidget.setObjectName(u"settingscentralwidget")
        sizePolicy.setHeightForWidth(self.settingscentralwidget.sizePolicy().hasHeightForWidth())
        self.settingscentralwidget.setSizePolicy(sizePolicy)
        self.verticalLayoutWidget_3 = QWidget(self.settingscentralwidget)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayoutWidget_3.setGeometry(QRect(0, 0, 651, 441))
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.horizontalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.GroupGeneral = QGroupBox(self.verticalLayoutWidget_3)
        self.GroupGeneral.setObjectName(u"GroupGeneral")
        self.LabelAppearance = QLabel(self.GroupGeneral)
        self.LabelAppearance.setObjectName(u"LabelAppearance")
        self.LabelAppearance.setGeometry(QRect(10, 20, 151, 16))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.LabelAppearance.setFont(font)
        self.ThemeSelectBox = QComboBox(self.GroupGeneral)
        self.ThemeSelectBox.setObjectName(u"comboBox_2")
        self.ThemeSelectBox.setGeometry(QRect(10, 40, 291, 24))
        self.ThemeSelectBox.addItem("light")
        self.ThemeSelectBox.addItem("dark")

        self.verticalLayout_2.addWidget(self.GroupGeneral)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.MemandCachebox = QGroupBox(self.verticalLayoutWidget_3)
        self.MemandCachebox.setObjectName(u"MemandCachebox")
        self.MaxAllocRAMBox = QSpinBox(self.MemandCachebox)
        self.MaxAllocRAMBox.setObjectName(u"MaxAllocRAMBox")
        self.MaxAllocRAMBox.setGeometry(QRect(180, 81, 81, 20))
        self.MaxAllocRAMBox.setMinimum(128)
        self.MaxAllocRAMBox.setMaximum(1000000)
        self.LabelMaxRAMUsage = QLabel(self.MemandCachebox)
        self.LabelMaxRAMUsage.setObjectName(u"LabelMaxRAMUseage")
        self.LabelMaxRAMUsage.setGeometry(QRect(59, 82, 131, 15))
        font1 = QFont()
        font1.setItalic(True)
        self.LabelMaxRAMUsage.setFont(font1)
        self.CacheAllToRAMButton = QRadioButton(self.MemandCachebox)
        self.CacheAllToRAMButton.setObjectName(u"CacheAllToRAMButton")
        self.CacheAllToRAMButton.setGeometry(QRect(10, 59, 231, 20))
        self.LoadAllFromDriveButton = QRadioButton(self.MemandCachebox)
        self.LoadAllFromDriveButton.setObjectName(u"LoadAllFromDriveButton")
        self.LoadAllFromDriveButton.setGeometry(QRect(10, 43, 231, 16))
        self.LabelDataManagementType = QLabel(self.MemandCachebox)
        self.LabelDataManagementType.setObjectName(u"LabelDataManagementType")
        self.LabelDataManagementType.setGeometry(QRect(10, 23, 151, 16))
        self.LabelDataManagementType.setFont(font)

        self.verticalLayout.addWidget(self.MemandCachebox)

        self.GroupAudio = QGroupBox(self.verticalLayoutWidget_3)
        self.GroupAudio.setObjectName(u"GroupAudio")
        self.OutputDeviceSelectionBox = QComboBox(self.GroupAudio)
        self.OutputDeviceSelectionBox.setObjectName(u"OutputDeviceSelectionBox")
        self.OutputDeviceSelectionBox.setGeometry(QRect(10, 40, 291, 24))
        self.LabelOutputDeice = QLabel(self.GroupAudio)
        self.LabelOutputDeice.setObjectName(u"LabelOutputDeice")
        self.LabelOutputDeice.setGeometry(QRect(10, 20, 151, 16))
        self.LabelOutputDeice.setFont(font)
        self.LalbelSampleRate = QLabel(self.GroupAudio)
        self.LalbelSampleRate.setObjectName(u"LalbelSampleRate")
        self.LalbelSampleRate.setGeometry(QRect(10, 70, 71, 16))
        # self.LabelBitDepth = QLabel(self.GroupAudio)
        # self.LabelBitDepth.setObjectName(u"LabelBitDepth")
        # self.LabelBitDepth.setGeometry(QRect(150, 70, 71, 16))
        self.LabelSampleRateValue = QLabel(self.GroupAudio)
        self.LabelSampleRateValue.setObjectName(u"LabelSampleRateValue")
        self.LabelSampleRateValue.setGeometry(QRect(20, 85, 121, 16))
        self.LabelSampleRateValue.setFont(font1)
        self.LabelSampleRateValue.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.LabelSampleRateValue.setToolTipDuration(3)
        # self.LabelBitDepthValue = QLabel(self.GroupAudio)
        # self.LabelBitDepthValue.setObjectName(u"LabelBitDepthValue")
        # self.LabelBitDepthValue.setGeometry(QRect(160, 85, 141, 16))
        # self.LabelBitDepthValue.setFont(font1)
        # self.LabelBitDepthValue.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        # self.LabelBitDepthValue.setToolTipDuration(3)

        self.verticalLayout.addWidget(self.GroupAudio)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.ConfirmButtons = QDialogButtonBox(self.verticalLayoutWidget_3)
        self.ConfirmButtons.setObjectName(u"ConfirmButtons")
        self.ConfirmButtons.setStandardButtons(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.ConfirmButtons.setCenterButtons(False)

        self.verticalLayout_3.addWidget(self.ConfirmButtons)

        self.verticalSpacer = QSpacerItem(0, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        SettingsWindow.setCentralWidget(self.settingscentralwidget)

        self.retranslateUi(SettingsWindow)

        QMetaObject.connectSlotsByName(SettingsWindow)

        self.UpdateAudioDevices()
        self.UpdateEverything()

        self.OutputDeviceSelectionBox.currentIndexChanged.connect(self.UpdateDeviceInfo)
        self.ConfirmButtons.accepted.connect(self.ApplySettings)
        self.ConfirmButtons.rejected.connect(SettingsWindow.close)
        self.ConfirmButtons.clicked.connect(self.ApplySettings)
        self.ConfirmButtons.clicked.connect(SettingsWindow.close)
        self.CacheAllToRAMButton.toggled.connect(self.CacheRadioButtonClicked)
        self.LoadAllFromDriveButton.toggled.connect(self.CacheRadioButtonClicked)

        self.GetSavedSettings()

    # setupUi

    def retranslateUi(self, SettingsWindow):
        SettingsWindow.setWindowTitle(QCoreApplication.translate("SettingsWindow", u"MainWindow", None))
        self.GroupGeneral.setTitle(QCoreApplication.translate("SettingsWindow", u"General", None))
        self.LabelAppearance.setText(QCoreApplication.translate("SettingsWindow", u"Appearance", None))
        self.MemandCachebox.setTitle(QCoreApplication.translate("SettingsWindow", u"Memory and Cache", None))
        self.LabelMaxRAMUsage.setText(QCoreApplication.translate("SettingsWindow", u"Max RAM useage (Mb)", None))
        self.CacheAllToRAMButton.setText(QCoreApplication.translate("SettingsWindow", u"Cache all to RAM  (Slow drives)", None))
        self.LoadAllFromDriveButton.setText(QCoreApplication.translate("SettingsWindow", u"Load all from drive", None))
        self.LabelDataManagementType.setText(QCoreApplication.translate("SettingsWindow", u"Data Management Type", None))
        self.GroupAudio.setTitle(QCoreApplication.translate("SettingsWindow", u"Audio", None))
        self.LabelOutputDeice.setText(QCoreApplication.translate("SettingsWindow", u"Output Device", None))
        self.LalbelSampleRate.setText(QCoreApplication.translate("SettingsWindow", u"Sample Rate:", None))
        # self.LabelBitDepth.setText(QCoreApplication.translate("SettingsWindow", u"Bit Depth:", None))
        self.LabelSampleRateValue.setText(QCoreApplication.translate("SettingsWindow", u"44.100Hz", None))
        # self.LabelBitDepthValue.setText(QCoreApplication.translate("SettingsWindow", u"32b float", None))
    # retranslateUi

    # def closeEvent(self, event: QEvent):
    #     print("Windows Closed")
    #     self.
    #     event.accept()  #                                  FINISH THAT HERE 

    def GetAudioDevices(self):
        """
        Returns a list of available audio output devices.
        """
        # Placeholder for actual implementation
        p = pyaudio.PyAudio()
        devices = []
        for i in range(p.get_device_count()):
            devices.append(p.get_device_info_by_index(i)['name'])

        return devices
    
    def UpdateAudioDevices(self):
        """
        Updates the audio output device selection box with available devices.
        """
        devices = self.GetAudioDevices()
        self.OutputDeviceSelectionBox.clear()
        self.OutputDeviceSelectionBox.addItems(devices)

    def UpdateDeviceInfo(self):
        """
        Updates the sample rate and bit depth labels based on the selected device.
        """
        selected_device = self.OutputDeviceSelectionBox.currentIndex()
        p = pyaudio.PyAudio()
        device_info = p.get_device_info_by_index(selected_device)
        # print(device_info)
        sample_rate = device_info['defaultSampleRate']
        # bit_depth = device_info['defaultSampleFormat']

        #update labels
        self.LabelSampleRateValue.setText(f"{int(sample_rate)}Hz")
        # self.LabelBitDepthValue.setText(f"{bit_depth}b float" if bit_depth == pyaudio.paFloat32 else f"{bit_depth}b int")

    def UpdateEverything(self):
        """
        Updates all settings in the UI.
        """
        self.UpdateDeviceInfo()

    def DeviceNameToIndex(self, device_name):
        """
        Returns the index of the device with the given name.
        """
        devices = self.GetAudioDevices()
        if device_name in devices:
            return devices.index(device_name)
        return 0

    def GetSavedSettings(self):
        settings = QSettings("Vaven", "BaSlicer")
        settings.beginGroup("Audio")
        output_device = settings.value("OutputDevice", "Default")
        output_device_index = self.DeviceNameToIndex(output_device)
        # Set the output device index in the combo box
        self.OutputDeviceSelectionBox.setCurrentIndex(output_device_index)

        settings.endGroup()
        settings.beginGroup("Memory")
        cache_type = settings.value("CacheType", "LoadAllFromDrive")
        max_ram_usage = settings.value("MaxRAMUsage", 1024, type=int)
        if cache_type == "CacheAllToRAM":
            self.CacheAllToRAMButton.setChecked(True)
        else:
            self.LoadAllFromDriveButton.setChecked(True)
        self.MaxAllocRAMBox.setValue(max_ram_usage)
        settings.endGroup()
        settings.beginGroup("General")
        theme = settings.value("Theme", "light")
        settings.endGroup()

        self.ThemeSelectBox.setCurrentText(theme)

    def ApplySettings(self):
        """
        Applies the current settings to the application.
        """
        settings = QSettings("Vaven", "BaSlicer")
        settings.beginGroup("Audio")
        settings.setValue("OutputDevice", self.OutputDeviceSelectionBox.currentText())
        settings.endGroup()

        settings.beginGroup("Memory")
        if self.CacheAllToRAMButton.isChecked():
            settings.setValue("CacheType", "CacheAllToRAM")
        else:
            settings.setValue("CacheType", "LoadAllFromDrive")
        settings.setValue("MaxRAMUsage", self.MaxAllocRAMBox.value())
        settings.endGroup()
        settings.beginGroup("General")
        settings.setValue("Theme", self.ThemeSelectBox.currentText())
        settings.endGroup()

    def CacheRadioButtonClicked(self):
        """
        Handles the cache radio button click event.
        """
        if self.CacheAllToRAMButton.isChecked():
            self.MaxAllocRAMBox.setEnabled(True)
            self.LabelMaxRAMUsage.setStyleSheet("color: black;")

        else:
            self.MaxAllocRAMBox.setEnabled(False)
            self.LabelMaxRAMUsage.setStyleSheet("color: gray;")




