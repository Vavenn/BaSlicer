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
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialogButtonBox, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QMainWindow,
    QRadioButton, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        if not SettingsWindow.objectName():
            SettingsWindow.setObjectName(u"SettingsWindow")
        SettingsWindow.resize(652, 443)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(SettingsWindow.sizePolicy().hasHeightForWidth())
        SettingsWindow.setSizePolicy(sizePolicy)
        self.actionNew = QAction(SettingsWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(SettingsWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(SettingsWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_As = QAction(SettingsWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionExit = QAction(SettingsWindow)
        self.actionExit.setObjectName(u"actionExit")
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
        self.groupBox_2 = QGroupBox(self.verticalLayoutWidget_3)
        self.groupBox_2.setObjectName(u"groupBox_2")

        self.verticalLayout_2.addWidget(self.groupBox_2)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.MemandCachebox = QGroupBox(self.verticalLayoutWidget_3)
        self.MemandCachebox.setObjectName(u"MemandCachebox")
        self.MaxAllocRAMBox = QSpinBox(self.MemandCachebox)
        self.MaxAllocRAMBox.setObjectName(u"MaxAllocRAMBox")
        self.MaxAllocRAMBox.setGeometry(QRect(180, 81, 81, 20))
        self.LabelMaxRAMUseage = QLabel(self.MemandCachebox)
        self.LabelMaxRAMUseage.setObjectName(u"LabelMaxRAMUseage")
        self.LabelMaxRAMUseage.setGeometry(QRect(59, 82, 131, 15))
        font = QFont()
        font.setItalic(True)
        self.LabelMaxRAMUseage.setFont(font)
        self.CacheAllToRAMButton = QRadioButton(self.MemandCachebox)
        self.CacheAllToRAMButton.setObjectName(u"CacheAllToRAMButton")
        self.CacheAllToRAMButton.setGeometry(QRect(10, 59, 231, 20))
        self.LoadAllFromDriveButton = QRadioButton(self.MemandCachebox)
        self.LoadAllFromDriveButton.setObjectName(u"LoadAllFromDriveButton")
        self.LoadAllFromDriveButton.setGeometry(QRect(10, 43, 231, 16))
        self.label = QLabel(self.MemandCachebox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 23, 151, 16))
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        self.label.setFont(font1)

        self.verticalLayout.addWidget(self.MemandCachebox)

        self.groupBox = QGroupBox(self.verticalLayoutWidget_3)
        self.groupBox.setObjectName(u"groupBox")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(110, 50, 49, 16))

        self.verticalLayout.addWidget(self.groupBox)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(self.verticalLayoutWidget_3)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout_3.addWidget(self.buttonBox)

        SettingsWindow.setCentralWidget(self.settingscentralwidget)

        self.retranslateUi(SettingsWindow)

        QMetaObject.connectSlotsByName(SettingsWindow)
    # setupUi

    def retranslateUi(self, SettingsWindow):
        SettingsWindow.setWindowTitle(QCoreApplication.translate("SettingsWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("SettingsWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("SettingsWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("SettingsWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("SettingsWindow", u"Save As...", None))
        self.actionExit.setText(QCoreApplication.translate("SettingsWindow", u"Exit", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("SettingsWindow", u"General", None))
        self.MemandCachebox.setTitle(QCoreApplication.translate("SettingsWindow", u"Memory and Cache", None))
        self.LabelMaxRAMUseage.setText(QCoreApplication.translate("SettingsWindow", u"Max RAM useage (Mb)", None))
        self.CacheAllToRAMButton.setText(QCoreApplication.translate("SettingsWindow", u"Cache all to RAM  (Slow drives)", None))
        self.LoadAllFromDriveButton.setText(QCoreApplication.translate("SettingsWindow", u"Load all from drive", None))
        self.label.setText(QCoreApplication.translate("SettingsWindow", u"Data Management Type", None))
        self.groupBox.setTitle(QCoreApplication.translate("SettingsWindow", u"Audio", None))
        self.label_2.setText(QCoreApplication.translate("SettingsWindow", u"todo!", None))
    # retranslateUi

