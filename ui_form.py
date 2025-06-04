from ast import Import
import pickle
from re import U
import sys
import os
import select
import struct
from tabnanny import check
from tracemalloc import start
# import wave
import PyWave
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QTableWidget, QTableWidgetItem, 
    QGroupBox, QLineEdit, QPushButton, QLabel, QSpinBox, QCheckBox, QComboBox, 
    QSlider, QFileDialog, QProgressDialog, QAbstractItemView, QSizePolicy, 
    QMenuBar, QMenu, QWidget, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem
)
from PySide6 import QtCore
from PySide6.QtMultimedia import QAudioOutput, QAudioFormat
from PySide6.QtCore import QRect, QSettings, QMetaObject, QCoreApplication, Qt, QSize, QPoint
from PySide6.QtGui import QCloseEvent, QAction, QFont, QIcon
import numpy as np
from scipy.signal import correlate
import pyqtgraph as pg
import pyaudio
import contextlib
import qdarktheme
from memory_profiler import profile

from settings import Ui_SettingsWindow

_current_stream = None

NOTE_NAMES = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
]


class AudioFile:
    def __init__(self, name, file_path, channels, sample_rate, bit_depth, length):
        self.name = name
        self.file_path = file_path
        self.channels = channels
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.length = length

    def __repr__(self):
        return f"AudioFile({self.name}, {self.file_path}, {self.channels}, {self.sample_rate}, {self.bit_depth}, {self.length})"

class SampleGroup:
    def __init__(self, name, audio_files=None):
        self.name = name
        self.audio_files = audio_files if audio_files is not None else []

    def add_audio_file(self, audio_file):
        self.audio_files.append(audio_file)

    def remove_audio_file(self, audio_file):
        self.audio_files.remove(audio_file)

    def __repr__(self):
        return f"SampleGroup({self.name}, {self.audio_files})"

class AudioSample:
    def __init__(self, start, end, samples=None, SR=44100):

        self.start = start
        self.end = end
        self.samples = samples if samples is not None else [[]] # 2d array
        self.SR = SR
        self.channels = len(self.samples)

class Slice:
    def __init__(self, start, end, sample_groups, analyzed=False, note=None, rr=None, UID=None):
        self.start = start
        self.end = end
        self.sample_groups = sample_groups 
        self.analyzed = analyzed
        self.note = note
        self.rr = rr
        self.UID = UID

    def __repr__(self):
        return f"Slice({self.start}, {self.end}, {self.sample_groups})"

class ClipboardSpinBox(QSpinBox):
    def __init__(self, parent=None, paste_callback=None):
        super().__init__(parent)
        self.paste_callback = paste_callback

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.paste_callback:
            self.paste_callback()

class SettingsWindow(QMainWindow):
    def __init__(self, parent=None, main_ui=None):
        super().__init__(parent)
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Settings - BaSlicer")
        self.main_ui = main_ui  # Store reference to main UI

    def closeEvent(self, event):
        if self.main_ui:
            self.main_ui.MainApplySettings()
        super().closeEvent(event)


class Ui_MainWindow(object):
    def __init__(self):
        self.Saved = False
        
        self.VERSION = "0.2.0"
        self.AUDIOFILES = []
        self.SGROUPS = []
        self.SLICES = []

        self.CACHEDAUDIOFILES = [] # tuples of audio name, audio data

        self.SliceTabSelectedSGroups = []

        self.UIDCounter = 0

    def closeEvent(self, event):
        if not self.Saved:
            self.NotSavedPrompt("a")
        self.SaveWindowSize()
        print("Closing application...")
        event.accept()

    def setupUi(self, MainWindow):
        
        DEV = True
        self.audio_output = QAudioOutput()
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1227, 604)
        

        self.LoadWindowSize()

        self.project_file_path = ""



            #       TOP BAR ACTIONS

        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionNew.triggered.connect(self.NewProject)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionOpen.triggered.connect(self.LoadSaveFile)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave.triggered.connect(self.SaveProject)
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionExit.triggered.connect(self.Exit)
        
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1227, 21))
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menuBar)

        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.menuEdit = self.menuBar.addMenu("Edit")
        self.SettingsAction = QAction(MainWindow)
        self.SettingsAction.setObjectName(u"SettingsAction")
        self.SettingsAction.setText("Settings")
        self.SettingsAction.triggered.connect(self.DisplaySettings)
        self.menuEdit.addAction(self.SettingsAction)

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.MainTabs = QTabWidget(self.centralwidget)
        MainTabsLayout = QVBoxLayout(self.centralwidget)
        MainTabsLayout.addWidget(self.MainTabs)
        self.centralwidget.setLayout(MainTabsLayout)

            #           IMPORT TAB

        self.Import = QWidget()
        self.Import.setObjectName(u"Import")
        ImportLayout = QHBoxLayout(self.Import)
        self.Import.setLayout(ImportLayout)

        # Left part
        LeftColumnLayout = QVBoxLayout()

        # Audio Files Group
        self.AudioFilesListGroup = QGroupBox(self.Import)
        self.AudioFilesListGroup.setObjectName(u"AudioFilesListGroup")
        AudioFilesListGroupLayout = QVBoxLayout(self.AudioFilesListGroup)

        self.AudioFilesList = QTableWidget(self.AudioFilesListGroup)
        self.AudioFilesList.verticalHeader().setVisible(False)
        self.AudioFilesList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.AudioFilesList.setObjectName(u"AudioFilesList")
        self.AudioFilesList.setColumnCount(7)
        self.AudioFilesList.setHorizontalHeaderLabels(("Name", "File", "Channels", "Sample Rate", "Bit Depth", "Lenght", "id"))
        AudioFilesTableWidths = ((0,80),(1,284),(2,55),(3,75),(4,55),(5,60),(6,30))
        for i in AudioFilesTableWidths:
            self.AudioFilesList.setColumnWidth(i[0],i[1])
        self.AudioFilesList.setSelectionBehavior(QTableWidget.SelectRows)
        AudioFilesListGroupLayout.addWidget(self.AudioFilesList)

        self.RemoveSelecteAudioButton = QPushButton(self.AudioFilesListGroup)
        self.RemoveSelecteAudioButton.setObjectName(u"RemoveSelecteAudioButton")
        self.RemoveSelecteAudioButton.setText("Remove Audio")
        self.RemoveSelecteAudioButton.clicked.connect(self.RemoveAudiofile)
        AudioFilesListGroupLayout.addWidget(self.RemoveSelecteAudioButton)

        self.AudioFilesListGroup.setLayout(AudioFilesListGroupLayout)
        

        # Import Recording Group
        self.ImportRecordingGroupBox = QGroupBox(self.Import)
        self.ImportRecordingGroupBox.setObjectName(u"ImportRecordingGroupBox")
        ImportRecordingLayout = QVBoxLayout(self.ImportRecordingGroupBox)

        SelectFileLayout = QHBoxLayout()
        ImportRecordingLayout.addLayout(SelectFileLayout)

        self.ImportRecordingSelectFileButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingSelectFileButton.setObjectName(u"ImportRecordingSelectFileButton")
        self.ImportRecordingSelectFileButton.setText("Select File")
        self.ImportRecordingSelectFileButton.clicked.connect(self.ImportAudioFile)
        SelectFileLayout.addWidget(self.ImportRecordingSelectFileButton)

        self.ImportRecordingDataPath = QLineEdit(self.ImportRecordingGroupBox)
        self.ImportRecordingDataPath.setObjectName(u"ImportRecordingDataPath")
        SelectFileLayout.addWidget(self.ImportRecordingDataPath)

        RecordingNameLayout = QHBoxLayout()
        ImportRecordingLayout.addLayout(RecordingNameLayout)

        self.NameInprojectLabel = QLabel(self.ImportRecordingGroupBox)
        self.NameInprojectLabel.setObjectName(u"NameInprojectLabel")
        self.NameInprojectLabel.setText("Name in project")
        RecordingNameLayout.addWidget(self.NameInprojectLabel)

        self.ImportRecordingName = QLineEdit(self.ImportRecordingGroupBox)
        self.ImportRecordingName.setObjectName(u"ImportRecordingName")
        RecordingNameLayout.addWidget(self.ImportRecordingName)

        self.ImportRecordingButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingButton.setObjectName(u"ImportRecordingButton")
        self.ImportRecordingButton.setText("Import")
        self.ImportRecordingButton.clicked.connect(self.ValidateAudioImport)
        ImportRecordingLayout.addWidget(self.ImportRecordingButton)

        self.ImportRecordingGroupBox.setLayout(ImportRecordingLayout)
        LeftColumnLayout.addWidget(self.ImportRecordingGroupBox)
        LeftColumnLayout.addWidget(self.AudioFilesListGroup)

        ImportLayout.addLayout(LeftColumnLayout, 2)

        # Right part
        self.SampleGroupConfig = QGroupBox(self.Import)
        self.SampleGroupConfig.setObjectName(u"SampleGroupConfig")
        SampleGroupConfigLayout = QVBoxLayout(self.SampleGroupConfig)

        self.ImporttabSampleGroupList = QTableWidget(self.SampleGroupConfig)
        self.ImporttabSampleGroupList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ImporttabSampleGroupList.setObjectName(u"ImporttabSampleGroupList")
        self.ImporttabSampleGroupList.setColumnCount(3)
        self.ImporttabSampleGroupList.setColumnWidth(0, 190)
        self.ImporttabSampleGroupList.verticalHeader().setVisible(False)
        self.ImporttabSampleGroupList.horizontalHeader().setVisible(False)
        self.ImporttabSampleGroupList.setSelectionBehavior(QTableWidget.SelectRows)
        self.ImporttabSampleGroupList.setSelectionMode(QTableWidget.SingleSelection)
        self.ImporttabSampleGroupList.clicked.connect(self.UpdateImportTabSGroupContentPreview)
        SampleGroupConfigLayout.addWidget(self.ImporttabSampleGroupList)

        self.AddSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        self.AddSampleGroupBox.setObjectName(u"AddSampleGroupBox")
        AddSampleGroupBoxLayout = QHBoxLayout(self.AddSampleGroupBox)
        self.AddSampleGroupNameEdit = QLineEdit(self.AddSampleGroupBox)
        self.AddSampleGroupNameEdit.setObjectName(u"AddSampleGroupNameEdit")
        AddSampleGroupBoxLayout.addWidget(self.AddSampleGroupNameEdit)
        self.AddSampleGroupconfirm = QPushButton(self.AddSampleGroupBox)
        self.AddSampleGroupconfirm.setObjectName(u"AddSampleGroupconfirm")
        self.AddSampleGroupconfirm.setText("+")
        self.AddSampleGroupconfirm.clicked.connect(self.AddNewSGroup)
        AddSampleGroupBoxLayout.addWidget(self.AddSampleGroupconfirm)
        self.AddSampleGroupBox.setLayout(AddSampleGroupBoxLayout)
        SampleGroupConfigLayout.addWidget(self.AddSampleGroupBox)

        # self.RenameSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        # self.RenameSampleGroupBox.setObjectName(u"RenameSampleGroupBox")
        # RenameSampleGroupBoxLayout = QHBoxLayout(self.RenameSampleGroupBox)
        # self.RenameSampleGroupEdit = QLineEdit(self.RenameSampleGroupBox)
        # self.RenameSampleGroupEdit.setObjectName(u"RenameSampleGroupEdit")
        # RenameSampleGroupBoxLayout.addWidget(self.RenameSampleGroupEdit)
        # self.RenameSampleGroupConfig = QPushButton(self.RenameSampleGroupBox)
        # self.RenameSampleGroupConfig.setObjectName(u"RenameSampleGroupConfig")
        # self.RenameSampleGroupConfig.setText(">");
        # # self.RenameSampleGroupConfig.clicked.connect(self.rename_sample_group)
        # RenameSampleGroupBoxLayout.addWidget(self.RenameSampleGroupConfig)
        # self.RenameSampleGroupBox.setLayout(RenameSampleGroupBoxLayout)
        # SampleGroupConfigLayout.addWidget(self.RenameSampleGroupBox)

        self.SampleGroupEdit = QGroupBox(self.SampleGroupConfig)
        self.SampleGroupEdit.setObjectName(u"SampleGroupEdit")
        SampleGroupEditLayout = QHBoxLayout(self.SampleGroupEdit)
        self.SampleGroupRemove = QPushButton(self.SampleGroupEdit)
        self.SampleGroupRemove.setObjectName(u"SampleGroupRemove")
        self.SampleGroupRemove.setText("Remove")
        self.SampleGroupRemove.clicked.connect(self.RemoveSampleGroup)
        SampleGroupEditLayout.addWidget(self.SampleGroupRemove)
        self.SampleGroupClone = QPushButton(self.SampleGroupEdit)
        self.SampleGroupClone.setObjectName(u"SampleGroupClone")
        self.SampleGroupClone.setText("Clone")
        self.SampleGroupClone.clicked.connect(self.CloneSampleGroup)
        SampleGroupEditLayout.addWidget(self.SampleGroupClone)
        self.SampleGroupEdit.setLayout(SampleGroupEditLayout)
        SampleGroupConfigLayout.addWidget(self.SampleGroupEdit)

        self.SampleGroupContentsLabel = QLabel(self.SampleGroupConfig)
        self.SampleGroupContentsLabel.setObjectName(u"SampleGroupContentsLabel")
        self.SampleGroupContentsLabel.setText("Contents")
        SampleGroupConfigLayout.addWidget(self.SampleGroupContentsLabel)

        self.SampleGroupContentsPreview = QTableWidget(self.SampleGroupConfig)
        self.SampleGroupContentsPreview.setObjectName(u"SampleGroupContentsPreview")
        self.SampleGroupContentsPreview.setColumnCount(1)
        self.SampleGroupContentsPreview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.SampleGroupContentsPreview.verticalHeader().setVisible(False)
        self.SampleGroupContentsPreview.horizontalHeader().setVisible(False)
        SampleGroupConfigLayout.addWidget(self.SampleGroupContentsPreview)

        self.AddAudioToSGroupButton = QPushButton(self.SampleGroupConfig)
        self.AddAudioToSGroupButton.setObjectName(u"AddAudioToSGroup")
        self.AddAudioToSGroupButton.setText("Add audio to current group")
        self.AddAudioToSGroupButton.clicked.connect(self.AddAudioToSGroup)
        SampleGroupConfigLayout.addWidget(self.AddAudioToSGroupButton)

        self.RemoveAudioGromSGroup = QPushButton(self.SampleGroupConfig)
        self.RemoveAudioGromSGroup.setObjectName(u"RemoveAudioGromSGroup")
        self.RemoveAudioGromSGroup.setText("Remove from current group")
        SampleGroupConfigLayout.addWidget(self.RemoveAudioGromSGroup)

        self.SampleGroupConfig.setLayout(SampleGroupConfigLayout)
        ImportLayout.addWidget(self.SampleGroupConfig, 2)

        self.MainTabs.addTab(self.Import, "")

                                                       #    SLICE TAB

        self.Slice = QWidget()
        self.Slice.setObjectName(u"Slice")
        SliceMainLayout = QVBoxLayout(self.Slice)
        

        self.SliceAudioEdition = QGroupBox(self.Slice)
        self.SliceAudioEdition.setObjectName(u"SliceAudioEdition")
        SliceAudioEditionLayout = QVBoxLayout(self.SliceAudioEdition)

        # self.SliceAudioContainer = QWidget(self.SliceAudioEdition)
        # AudioPreviewContainerLayout = QVBoxLayout(self.SliceAudioContainer)
        # self.SliceWaveformVisu = pg.PlotWidget(self.SliceAudioContainer)
        # self.SliceWaveformVisu.setObjectName(u"AudioPreviewPlaceholder")
        # self.SliceWaveformVisu.setBackground("lightgray")
        # self.SliceWaveformVisu.showGrid(x=False, y=False)
        # self.SliceWaveformVisu.getPlotItem().hideAxis("bottom")
        # self.SliceWaveformVisu.getPlotItem().hideAxis("left")
        # self.SliceWaveformVisu.getPlotItem().setMenuEnabled(False)
        # self.SliceWaveformVisu.getPlotItem().setLimits(yMin=-1, yMax=1)
        # self.SliceWaveformVisu.setMouseEnabled(x=True, y=False)
        # self.SliceWaveformVisu.plotItem.setMenuEnabled(False)
        # self.SliceWaveformVisu.plotItem.setMouseEnabled(y=False)
        # self.SliceWaveformVisu.sigXRangeChanged.connect(self.on_waveform_view_changed)
        # AudioPreviewContainerLayout.addWidget(self.SliceWaveformVisu)
        # self.SliceAudioContainer.setLayout(AudioPreviewContainerLayout)
        # SliceAudioEditionLayout.addWidget(self.SliceAudioContainer)
        SliceMainLayout.addWidget(self.SliceAudioEdition)

        # --- Audio File Selection for Slice Waveform ---
        AudioFileSelectLayout = QHBoxLayout()
        # self.SliceAudioFileSelectLabel = QLabel(self.SliceAudioEdition)
        # self.SliceAudioFileSelectLabel.setText("Audio File:")
        # AudioFileSelectLayout.addWidget(self.SliceAudioFileSelectLabel)

        # self.SliceAudioFileSelect = QComboBox(self.SliceAudioEdition)
        # self.SliceAudioFileSelect.setObjectName(u"SliceAudioFileSelect")
        # self.SliceAudioFileSelect.currentIndexChanged.connect(self.SliceAudioWaveformUpdate)
        # AudioFileSelectLayout.addWidget(self.SliceAudioFileSelect)

        # Optionally, connect to a method to update the waveform when selection changes
        # self.SliceAudioFileSelect.currentIndexChanged.connect(self.UpdateSliceWaveform)

        SliceAudioEditionLayout.addLayout(AudioFileSelectLayout)


        # --- Top Controls (Sample Group selection, cutpoint, end, buttons) ---
        TopControlsLayout = QHBoxLayout()

        # Sample Group Selection and buttons (left)
        SGroupsLayout = QVBoxLayout()
        self.labelsamplegroups = QLabel(self.Slice)
        self.labelsamplegroups.setObjectName(u"labelsamplegroups")
        

        self.SampleGroupSelection = QTableWidget(self.Slice)
        self.SampleGroupSelection.setObjectName(u"SampleGroupSelection")
        self.SampleGroupSelection.setColumnCount(4)
        self.SampleGroupSelection.setColumnWidth(0, 138)
        self.SampleGroupSelection.setColumnWidth(1, 10)
        self.SampleGroupSelection.setColumnWidth(2, 10)
        self.SampleGroupSelection.setColumnWidth(3, 10)
        self.SampleGroupSelection.verticalHeader().setVisible(False)
        self.SampleGroupSelection.horizontalHeader().setVisible(False)
        self.SampleGroupSelection.clicked.connect(self.UpdateSelectedSGroup)
        # self.SampleGroupSelection.clicked.connect(self.PopulateSliceTabAudioPreviewBox)
        

        SGroupsButtonsLayout = QHBoxLayout()
        self.SliceGroupAllButton = QPushButton(self.Slice)
        self.SliceGroupAllButton.setObjectName(u"SliceGroupAllButton")
        self.SliceGroupAllButton.setText("All")
        self.SliceGroupAllButton.clicked.connect(self.SelectAllSampleGroups)
        

        self.SliceGroupClearButton = QPushButton(self.Slice)
        self.SliceGroupClearButton.setObjectName(u"SliceGroupClearButton")
        self.SliceGroupClearButton.setText("Clear")
        self.SliceGroupClearButton.clicked.connect(self.ClearAllSampleGroups)
        SGroupsButtonsLayout.addWidget(self.labelsamplegroups)
        SGroupsButtonsLayout.addWidget(self.SliceGroupAllButton)
        SGroupsButtonsLayout.addWidget(self.SliceGroupClearButton)
        
        SGroupsLayout.addLayout(SGroupsButtonsLayout)
        SGroupsLayout.addWidget(self.SampleGroupSelection)

        TopControlsLayout.addLayout(SGroupsLayout, 1)

        # Sample Cut Controls (center)
        CutControlsLayout = QVBoxLayout()
        CutInputsLayout = QHBoxLayout()

        self.labelsamplestart = QLabel(self.Slice)
        self.labelsamplestart.setObjectName(u"labelsamplestart")
        self.labelsamplestart.setText("Sample Start")
        CutInputsLayout.addWidget(self.labelsamplestart)

        self.SampleCutpointInput = ClipboardSpinBox(self.Slice, None)
        self.SampleCutpointInput.setObjectName(u"SampleCutpointInput")
        self.SampleCutpointInput.setMinimum(0)
        self.SampleCutpointInput.setMaximum(999999999)
        CutInputsLayout.addWidget(self.SampleCutpointInput)

        self.labelsampleend = QLabel(self.Slice)
        self.labelsampleend.setObjectName(u"labelsampleend")
        self.labelsampleend.setText("Sample End")
        CutInputsLayout.addWidget(self.labelsampleend)

        self.SampleEndInput = ClipboardSpinBox(self.Slice, None)
        self.SampleEndInput.setObjectName(u"SampleEndInput")
        self.SampleEndInput.setMaximum(999999999)
        CutInputsLayout.addWidget(self.SampleEndInput)

        self.IsLengthCheckbox = QCheckBox(self.Slice)
        self.IsLengthCheckbox.setObjectName(u"IsLengthCheckbox")
        self.IsLengthCheckbox.setText("Len")
        CutInputsLayout.addWidget(self.IsLengthCheckbox)

        CutControlsLayout.addLayout(CutInputsLayout)

        # Add/Remove Buttons (below inputs)
        CutButtonsLayout = QHBoxLayout()
        self.Add_Sample_Cut_Data = QPushButton(self.Slice)
        self.Add_Sample_Cut_Data.setObjectName(u"Add_Sample_Cut_Data")
        self.Add_Sample_Cut_Data.setText("+")
        self.Add_Sample_Cut_Data.clicked.connect(self.AddNewSlice)
        CutInputsLayout.addWidget(self.Add_Sample_Cut_Data)

        self.Remove_Sample_Cut_Data = QPushButton(self.Slice)
        self.Remove_Sample_Cut_Data.setObjectName(u"Remove_Sample_Cut_Data")
        self.Remove_Sample_Cut_Data.setText("Remove Row")
        CutInputsLayout.addWidget(self.Remove_Sample_Cut_Data)

        self.AutoClipboardCheckbox = QCheckBox(self.Slice)
        self.AutoClipboardCheckbox.setObjectName(u"AutoClipboardCheckbox")
        self.AutoClipboardCheckbox.setText("Auto Clipboard")
        CutInputsLayout.addWidget(self.AutoClipboardCheckbox)

        CutControlsLayout.addLayout(CutButtonsLayout)
        TopControlsLayout.addLayout(CutControlsLayout, 2)

        # Wrap TopControlsLayout
        TopControlsWidget = QWidget(self.Slice)
        TopControlsWidget.setLayout(TopControlsLayout)
        TopControlsWidget.setFixedHeight(180)  #

        SliceMainLayout.addWidget(TopControlsWidget)

        # --- Sample Cut Data Table 
        self.Sample_Cut_Data_Table = QTableWidget(self.Slice)
        self.Sample_Cut_Data_Table.setObjectName(u"Sample_Cut_Data_Table")
        self.Sample_Cut_Data_Table.setColumnCount(5)
        self.Sample_Cut_Data_Table.setHorizontalHeaderLabels(("ID", "S. Start", "S. End", "Length", "Sample Groups"))
        self.Sample_Cut_Data_Table.verticalHeader().setVisible(False)
        self.Sample_Cut_Data_Table.setSelectionBehavior(QTableWidget.SelectRows)
        self.Sample_Cut_Data_Table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        SliceMainLayout.addWidget(self.Sample_Cut_Data_Table)

        self.Slice.setLayout(SliceMainLayout)
        self.MainTabs.addTab(self.Slice, "")

                                                              #    SORT TAB    
 
        self.Sort = QWidget()
        self.Sort.setObjectName(u"Sort")
        SortMainLayout = QVBoxLayout(self.Sort)

        # --- Top Row: SGroup Filter and Slices List (left), Audio Preview + Configs (center) ---
        TopRowLayout = QHBoxLayout()

        # SGroup Filter (left)
        SGroupFilterLayout = QVBoxLayout()
        self.SortTabSGroupfilter = QComboBox(self.Sort)
        self.SortTabSGroupfilter.addItem("SGroup Filter")
        self.SortTabSGroupfilter.setObjectName(u"SortTabSGroupfilter")
        self.SortTabSGroupfilter.currentIndexChanged.connect(self.SortTabSliceListUpdate)
        SGroupFilterLayout.addWidget(self.SortTabSGroupfilter)

        self.SortGroupSlices = QGroupBox(self.Sort)
        self.SortGroupSlices.setObjectName(u"SortGroupSlices")
        SortGroupSlicesLayout = QVBoxLayout(self.SortGroupSlices)

        self.SortTabSliceList = QTableWidget(self.SortGroupSlices)
        self.SortTabSliceList.setObjectName(u"SortTabSliceList")
        self.SortTabSliceList.setColumnCount(4)
        self.SortTabSliceList.setColumnWidth(0, 40)
        self.SortTabSliceList.setColumnWidth(1, 60)
        self.SortTabSliceList.setColumnWidth(2, 60)
        self.SortTabSliceList.setColumnWidth(3, 40)
        self.SortTabSliceList.setHorizontalHeaderLabels(("ID", "S. Start", "S. End", "SGroups"))
        self.SortTabSliceList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.SortTabSliceList.setSelectionMode(QTableWidget.SingleSelection)
        self.SortTabSliceList.setSelectionBehavior(QTableWidget.SelectRows)
        self.SortTabSliceList.horizontalHeader().setVisible(False)
        if not DEV:
            self.SortTabSliceList.hideColumn(0)
            self.SortTabSliceList.hideColumn(3)
        #self.SortTabSliceList.itemSelectionChanged.connect(self.update_waveform_preview)
        self.SortTabSliceList.itemSelectionChanged.connect(self.SortTabAudioAnalysisUpdate)
        SortGroupSlicesLayout.addWidget(self.SortTabSliceList)
        self.SortGroupSlices.setLayout(SortGroupSlicesLayout)
        SGroupFilterLayout.addWidget(self.SortGroupSlices)
        TopRowLayout.addLayout(SGroupFilterLayout, 1)

        # --- Center: Audio Preview + Configs (vertical) ---
        CenterLayout = QVBoxLayout()

        # Audio Preview
        self.SortAudioPreview = QGroupBox(self.Sort)
        self.SortAudioPreview.setObjectName(u"SortAudioPreview")
        SortAudioPreviewLayout = QVBoxLayout(self.SortAudioPreview)

        self.AudioPreviewContainer = QWidget(self.SortAudioPreview)
        AudioPreviewContainerLayout = QVBoxLayout(self.AudioPreviewContainer)
        self.WaveformVisu = pg.PlotWidget(self.AudioPreviewContainer)
        self.WaveformVisu.setObjectName(u"AudioPreviewPlaceholder")
        self.WaveformVisu.setBackground("lightgray")
        self.WaveformVisu.showGrid(x=False, y=False)
        self.WaveformVisu.getPlotItem().hideAxis("bottom")
        self.WaveformVisu.getPlotItem().hideAxis("left")
        self.WaveformVisu.getPlotItem().setMenuEnabled(False)
        self.WaveformVisu.getPlotItem().setLimits(yMin=-1, yMax=1)
        self.WaveformVisu.setMouseEnabled(x=True, y=False)
        self.WaveformVisu.plotItem.setMenuEnabled(False)
        self.WaveformVisu.plotItem.setMouseEnabled(y=False)
        AudioPreviewContainerLayout.addWidget(self.WaveformVisu)
        self.AudioPreviewContainer.setLayout(AudioPreviewContainerLayout)
        SortAudioPreviewLayout.addWidget(self.AudioPreviewContainer)

        # Controls under waveform
        AudioPreviewControlsLayout = QHBoxLayout()
        self.SortPreviewPlayButton = QPushButton(self.SortAudioPreview)
        self.SortPreviewPlayButton.setObjectName(u"SortPreviewPlayButton")
        self.SortPreviewPlayButton.setText("Play")
        AudioPreviewControlsLayout.addWidget(self.SortPreviewPlayButton)

        self.SortPreviewStopButton = QPushButton(self.SortAudioPreview)
        self.SortPreviewStopButton.setObjectName(u"SortPreviewStopButton")
        self.SortPreviewStopButton.setText("Stop")
        AudioPreviewControlsLayout.addWidget(self.SortPreviewStopButton)

        self.LabelPlaybackVolume = QLabel(self.SortAudioPreview)
        self.LabelPlaybackVolume.setObjectName(u"LabelPlaybackVolume")
        self.LabelPlaybackVolume.setText("Playback Volume")
        AudioPreviewControlsLayout.addWidget(self.LabelPlaybackVolume)

        self.SortPreviewVolume = QSlider(self.SortAudioPreview)
        self.SortPreviewVolume.setObjectName(u"SortPreviewVolume")
        self.SortPreviewVolume.setOrientation(Qt.Orientation.Horizontal)
        self.SortPreviewVolume.setMaximum(10000)
        self.SortPreviewVolume.setSingleStep(1)
        self.SortPreviewVolume.setMinimum(0)
        self.SortPreviewVolume.setValue(10000)
        AudioPreviewControlsLayout.addWidget(self.SortPreviewVolume)

        self.SortPreviewAudioSelect = QComboBox(self.SortAudioPreview)
        self.SortPreviewAudioSelect.setObjectName(u"SortPreviewAudioSelect")
        self.SortPreviewAudioSelect.currentIndexChanged.connect(self.SortAudioWaveformUpdate)
        AudioPreviewControlsLayout.addWidget(self.SortPreviewAudioSelect)

        SortAudioPreviewLayout.addLayout(AudioPreviewControlsLayout)

        # Frequency/Note labels
        FreqNoteLayout = QHBoxLayout()
        # self.FrequencyLabel = QLabel(self.SortAudioPreview)
        # self.FrequencyLabel.setObjectName(u"FrequencyLabel")
        # self.FrequencyLabel.setText("Frequency: N/A")
        # FreqNoteLayout.addWidget(self.FrequencyLabel)
        self.NoteLabel = QLabel(self.SortAudioPreview)
        self.NoteLabel.setObjectName(u"NoteLabel")
        self.NoteLabel.setText("Note: N/A")
        FreqNoteLayout.addWidget(self.NoteLabel)
        SortAudioPreviewLayout.addLayout(FreqNoteLayout)

        self.SortAudioPreview.setLayout(SortAudioPreviewLayout)
        CenterLayout.addWidget(self.SortAudioPreview)

        # --- Add Sort Setup and Note Config under the waveform preview ---
        # self.SortSetup = QGroupBox(self.Sort)
        # self.SortSetup.setObjectName(u"SortSetup")
        # SortSetupLayout = QVBoxLayout(self.SortSetup)
        # self.LabelSortRRSelection = QLabel(self.SortSetup)
        # self.LabelSortRRSelection.setObjectName(u"LabelSortRRSelection")
        # self.LabelSortRRSelection.setText("Round Robins")
        # SortSetupLayout.addWidget(self.LabelSortRRSelection)
        # self.SortSetupRRSelection = QSpinBox(self.SortSetup)
        # self.SortSetupRRSelection.setObjectName(u"SortSetupRRSelection")
        # self.SortSetupRRSelection.setMinimum(1)
        # self.SortSetupRRSelection.setMaximum(10)
        # SortSetupLayout.addWidget(self.SortSetupRRSelection)
        # self.SortSetup.setLayout(SortSetupLayout)
        # CenterLayout.addWidget(self.SortSetup)

        self.SortNoteConfig = QGroupBox(self.Sort)
        self.SortNoteConfig.setObjectName(u"SortNoteConfig")
        self.SortNoteConfig.setTitle("Note Configuration")
        SortNoteConfigLayout = QVBoxLayout(self.SortNoteConfig)

        NoteConfigRow = QHBoxLayout()
        self.OctaveLabel = QLabel(self.SortNoteConfig)
        self.OctaveLabel.setObjectName(u"OctaveLabel")
        self.OctaveLabel.setText("Octave:")
        NoteConfigRow.addWidget(self.OctaveLabel)
        self.OctaveSelect = QSpinBox(self.SortNoteConfig)
        self.OctaveSelect.setObjectName(u"OctaveSelect")
        self.OctaveSelect.setMinimum(0)
        self.OctaveSelect.setMaximum(10)
        self.OctaveSelect.setValue(4)
        NoteConfigRow.addWidget(self.OctaveSelect)
        self.NoteLabelConfig = QLabel(self.SortNoteConfig)
        self.NoteLabelConfig.setObjectName(u"NoteLabelConfig")
        self.NoteLabelConfig.setText("Note:")
        NoteConfigRow.addWidget(self.NoteLabelConfig)
        self.NoteSelect = QComboBox(self.SortNoteConfig)
        self.NoteSelect.setObjectName(u"NoteSelect")
        self.NoteSelect.addItems(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        NoteConfigRow.addWidget(self.NoteSelect)
        self.RRLabel = QLabel(self.SortNoteConfig)
        self.RRLabel.setObjectName(u"RRLabel")
        self.RRLabel.setText("Round Robin:")
        NoteConfigRow.addWidget(self.RRLabel)
        self.RRSelect = QSpinBox(self.SortNoteConfig)
        self.RRSelect.setObjectName(u"RRSelect")
        self.RRSelect.setMinimum(1)
        self.RRSelect.setMaximum(10)
        self.RRSelect.setValue(1)
        NoteConfigRow.addWidget(self.RRSelect)
        SortNoteConfigLayout.addLayout(NoteConfigRow)

        NoteConfigButtonsLayout = QHBoxLayout()
        self.AcceptButton = QPushButton(self.SortNoteConfig)
        self.AcceptButton.setObjectName(u"AcceptButton")
        self.AcceptButton.setText("Accept")
        NoteConfigButtonsLayout.addWidget(self.AcceptButton)
        self.AcceptNextButton = QPushButton(self.SortNoteConfig)
        self.AcceptNextButton.setObjectName(u"AcceptNextButton")
        self.AcceptNextButton.setText("Accept+Next")
        NoteConfigButtonsLayout.addWidget(self.AcceptNextButton)
        self.DetectTransientButton = QPushButton(self.SortNoteConfig)
        self.DetectTransientButton.setObjectName(u"DetectTransientButton")
        self.DetectTransientButton.setText("Detect Transient")
        NoteConfigButtonsLayout.addWidget(self.DetectTransientButton)
        SortNoteConfigLayout.addLayout(NoteConfigButtonsLayout)

        self.SortNoteConfig.setLayout(SortNoteConfigLayout)
        CenterLayout.addWidget(self.SortNoteConfig)

        TopRowLayout.addLayout(CenterLayout, 2)

        SortMainLayout.addLayout(TopRowLayout)
        self.Sort.setLayout(SortMainLayout)
        self.MainTabs.addTab(self.Sort, "")

                                                            #   EXPORT TAB 

        self.Export = QWidget()
        self.Export.setObjectName(u"Export")

        self.ExportFinalTable = QTableWidget(self.Export)
        self.ExportFinalTable.setObjectName(u"ExportFinalTable")
        self.ExportFinalTable.setGeometry(QRect(10, 10, 800, 400))  # Adjust size and position as needed
        self.ExportFinalTable.setColumnCount(9)  # Update column count to 9
        self.ExportFinalTable.setHorizontalHeaderLabels([
            "ID", "Slice ID", "Sample Start", "Sample End", "Audio File Path", 
            "Sample Group Name", "MIDI Note", "Round Robin", "Start Offset"  # Add new column
        ])
        self.ExportFinalTable.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Make the table read-only
        self.ExportFinalTable.setSelectionMode(QAbstractItemView.NoSelection)  # Disable selection

         # Export Button
        self.ExportButton = QPushButton(self.Export)
        self.ExportButton.setObjectName(u"ExportButton")
        self.ExportButton.setGeometry(QRect(820, 10, 100, 30))  
        self.ExportButton.setText("Export")
        #self.ExportButton.clicked.connect(self.export_samples)
    
        self.ExportStartOffsetBox = QSpinBox(self.Export)
        self.ExportStartOffsetBox.setObjectName(u"ExportStartOffsetBox")
        self.ExportStartOffsetBox.setGeometry(QRect(820, 50, 100, 30))  
        self.ExportStartOffsetBox.setRange(-10000, 10000)  
        self.ExportStartOffsetBox.setValue(0)  # Default value
        self.ExportStartOffsetBox.setToolTip("Adjust the sample start offset for all exports.")

        self.MainTabs.addTab(self.Export, "")

        self.MainTabs.setCurrentIndex(0)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)
        self.MainApplySettings()
    # setupUi

    def retranslateUi(self, MainWindow):
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Import), QCoreApplication.translate("MainWindow", u"Import", None))
        self.Add_Sample_Cut_Data.setText(QCoreApplication.translate("MainWindow", u"+", None))
        self.IsLengthCheckbox.setText("")
        self.SliceGroupAllButton.setText(QCoreApplication.translate("MainWindow", u"All", None))
        self.SliceGroupClearButton.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.labelsamplegroups.setText(QCoreApplication.translate("MainWindow", u"Sample Groups", None))
        self.labelsamplestart.setText(QCoreApplication.translate("MainWindow", u"Sample Start", None))
        self.labelsampleend.setText(QCoreApplication.translate("MainWindow", u"Sample End", None))
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Slice), QCoreApplication.translate("MainWindow", u"Slice", None))
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Sort), QCoreApplication.translate("MainWindow", u"Sort", None))
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Export), QCoreApplication.translate("MainWindow", u"Export", None))
        self.SampleGroupConfig.setTitle(QCoreApplication.translate("MainWindow", u"Sample Groups", None))
        self.AddSampleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Add SGroup", None))
        self.AddSampleGroupNameEdit.setText("")
        self.AddSampleGroupconfirm.setText(QCoreApplication.translate("MainWindow", u"+", None))
        # self.RenameSampleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Rename Sgroup", None))
        # self.RenameSampleGroupEdit.setText("")
        # self.RenameSampleGroupConfig.setText(QCoreApplication.translate("MainWindow", u">", None))
        # self.SampleGroupMove.setTitle(QCoreApplication.translate("MainWindow", u"Move", None))
        # self.SampleGroupMoveUp.setText(QCoreApplication.translate("MainWindow", u"Up", None))
        # self.SampleGroupMoveDown.setText(QCoreApplication.translate("MainWindow", u"Down", None))
        self.SampleGroupEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.SampleGroupRemove.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.SampleGroupClone.setText(QCoreApplication.translate("MainWindow", u"Clone", None))
        self.SampleGroupContentsLabel.setText(QCoreApplication.translate("MainWindow", u"Contents", None))
        self.AddAudioToSGroupButton.setText(QCoreApplication.translate("MainWindow", u"Add audio to current group", None))
        self.RemoveAudioGromSGroup.setText(QCoreApplication.translate("MainWindow", u"Remove from current group", None))
        self.AudioFilesListGroup.setTitle(QCoreApplication.translate("MainWindow", u"Audio Files", None))
        self.ImportRecordingGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Import Recording", None))
        self.ImportRecordingButton.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.ImportRecordingName.setText("")
        self.NameInprojectLabel.setText(QCoreApplication.translate("MainWindow", u"Name in project", None))
        self.ImportRecordingDataPath.setText(QCoreApplication.translate("MainWindow", u"    . . .", None))
        self.ImportRecordingSelectFileButton.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.RemoveSelecteAudioButton.setText(QCoreApplication.translate("MainWindow", u"Remove Audio", None))
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Import), QCoreApplication.translate("MainWindow", u"Import", None))
        self.AddSampleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Add SGroup", None))
        self.AddSampleGroupNameEdit.setText("")
        self.AddSampleGroupconfirm.setText(QCoreApplication.translate("MainWindow", u"+", None))
        # self.RenameSampleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Rename Sgroup", None))
        # self.RenameSampleGroupEdit.setText("")
        # self.RenameSampleGroupConfig.setText(QCoreApplication.translate("MainWindow", u">", None))
        # self.SampleGroupMove.setTitle(QCoreApplication.translate("MainWindow", u"Move", None))
        # self.SampleGroupMoveUp.setText(QCoreApplication.translate("MainWindow", u"Up", None))
        # self.SampleGroupMoveDown.setText(QCoreApplication.translate("MainWindow", u"Down", None))
        self.SampleGroupEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.SampleGroupRemove.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.SampleGroupClone.setText(QCoreApplication.translate("MainWindow", u"Clone", None))
        self.SampleGroupContentsLabel.setText(QCoreApplication.translate("MainWindow", u"Contents", None))
        self.AddAudioToSGroupButton.setText(QCoreApplication.translate("MainWindow", u"Add audio to current group", None))
        self.RemoveAudioGromSGroup.setText(QCoreApplication.translate("MainWindow", u"Remove from current group", None))
        self.AudioFilesListGroup.setTitle(QCoreApplication.translate("MainWindow", u"Audio Files", None))

        self.ImportRecordingGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Import Recording", None))
        self.ImportRecordingButton.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.ImportRecordingName.setText("")
        self.NameInprojectLabel.setText(QCoreApplication.translate("MainWindow", u"Name in project", None))
        self.ImportRecordingDataPath.setText(QCoreApplication.translate("MainWindow", u"    . . .", None))
        self.ImportRecordingSelectFileButton.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Import), QCoreApplication.translate("MainWindow", u"Import", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As...", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.SortGroupSlices.setTitle(QCoreApplication.translate("MainWindow", u"Slices", None))
        self.SortTabSGroupfilter.setItemText(0, QCoreApplication.translate("MainWindow", u"SGroup Filter", None))
        self.SortAudioPreview.setTitle(QCoreApplication.translate("MainWindow", u"Audio Preview", None))
        self.SortPreviewPlayButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.SortPreviewStopButton.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.LabelPlaybackVolume.setText(QCoreApplication.translate("MainWindow", u"Playback Volume", None))
        # self.SortSetup.setTitle(QCoreApplication.translate("MainWindow", u"Setup", None))
        # self.LabelSortRRSelection.setText(QCoreApplication.translate("MainWindow", u"Round Robins", None))
    # retranslateUi

    def Exit(self):
        """
        Exit the application.
        """
        self.NotSavedPrompt("You have unsaved changes. Do you want to save before exiting?")
        print("Exiting application.")
        sys.exit()

    def ImportAudioFile(self):
        """
        File Opening Dialog, WAV only.
        """
        settings = QSettings("Vaven", "BaSlicer")
        last_dir = settings.value("lastWavImportDir", "")
        
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select a WAV file",
            last_dir,
            "WAV files (*.wav);;All files (*)"
        )
        if file_path:
            settings.setValue("lastWavImportDir", file_path)
            self.ImportRecordingDataPath.setText(file_path)
            return file_path

        
        return None

    def NotSavedPrompt(self, msg=None):
        if not self.Saved:
            reply = QMessageBox.question(
                None,
                "Unsaved Changes",
                msg,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Yes:
                self.SaveProject()
            elif reply == QMessageBox.Cancel:
                return

    def NewProject(self):
        """
        Create a new project
        """

        self.NotSavedPrompt("You have unsaved changes. Do you want to save before creating a new project?")

        self.AUDIOFILES = []
        self.SGROUPS = []
        self.SLICES = []
        self.CACHEDAUDIOFILES = []
        print("New project created.")

        # Update UI stuff
        self.UpdateEverything()

    def LoadSaveFile(self):
        """
        Load shtuff
        """

        self.NotSavedPrompt("You have unsaved changes. Do you want to save before loading a new project?")

        settings = QSettings("Vaven", "BaSlicer")
        last_dir = settings.value("lastProjectOpenDir", "")

        open_file, _ = QFileDialog.getOpenFileName(
            None,
            "Select a BaSlicer Project file",
            last_dir,
            "BasProject File (*.basproj);;All files (*)"
        )
        if open_file:
            settings.setValue("lastProjectOpenDir", open_file)
            self.project_file_path = open_file

            with open(open_file, "rb") as f:
                data = f.read()
                # Deserialize the data to get the project state
                if len(pickle.loads(data)) < 4:
                    print("Warning: Project file is corrupted or incompatible.")
                    return
                data_version = pickle.loads(data)[3]
                if data_version != self.VERSION or not data_version:
                    print(f"Warning: Project version {data_version} does not match current version {self.VERSION}, load aborted.")
                    return
                self.AUDIOFILES, self.SGROUPS, self.SLICES, _ = pickle.loads(data)

        # UID Stuff



        try:
            self.UIDCounter = max((slice.UID for slice in self.SLICES if slice.UID is not None), default=0) + 1
        except AttributeError:
            print("Error: One or more slices are missing the UID attribute.")
            self.UIDCounter = 1

        # Update the UI with loaded data
        self.UpdateEverything()

    def EnsureUniqueUIDs(self):
        """
        Ensure all Slice objects have unique UIDs.
        If duplicates are found, assign new unique UIDs.
        """
        self.UIDCounter = 0
        for slice in self.SLICES:
            self.UIDCounter += 1
            slice.UID = self.UIDCounter
            print(f"Assigned new UID {slice.UID} to slice with start {slice.start} and end {slice.end}.")
        print("All slices now have unique UIDs.")

    def SaveProject(self):
        """
        Save shtuff
        """
        settings = QSettings("Vaven", "BaSlicer")
        last_dir = settings.value("lastProjectSaveDir", "")

        if not self.project_file_path:
            save_file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Select a BaSlicer Project file",
                last_dir,
                "BasProject File (*.basproj);;All files (*)"
            )
            if not save_file_path:
                print("Save operation canceled.")
                return

            settings.setValue("lastProjectSaveDir", save_file_path)
            self.project_file_path = save_file_path


        # self.EnsureUniqueUIDs()

        with open(self.project_file_path, "wb") as f:
            pickle.dump(
                (self.AUDIOFILES, self.SGROUPS, self.SLICES, self.VERSION),
                f, pickle.HIGHEST_PROTOCOL)

        self.Saved = True

        print(f"Project saved to {self.project_file_path}")

    def ValidateAudioImport(self):
        """
        Adds audio to project as object.
        """
        rawpath = self.ImportRecordingDataPath.text()
        path = Path(rawpath)
        name = self.ImportRecordingName.text()

        for audio_file in self.AUDIOFILES:
            if audio_file.name == name:
                print(f"Audio file '{name}' already exists in the project.")
                return

        if path.is_file() and path.suffix.lower() == ".wav" and name:

            num_channels, sample_rate, bit_depth, num_frames = GetWavInfo(rawpath)

            new_audio_file = AudioFile(
                name=name,
                file_path=str(path),
                channels=num_channels,
                sample_rate=sample_rate,
                bit_depth=bit_depth,
                length=num_frames
            )

            self.AUDIOFILES.append(new_audio_file)

            # Update stuff
            self.UpdateImportTab()
            print(f"Audio file '{name}' added to the project.")
        else:
            print("Invalid file or missing name.")

    def AddNewSGroup(self):
        """
        Add a new empty sample group with the given name.
        """

        name = self.AddSampleGroupNameEdit.text()

        if not name:
            print("Sample group name cannot be empty.")
            return

        # Check if the group already exists
        for group in self.SGROUPS:
            if group.name == name:
                print(f"Sample group '{name}' already exists.")
                return

        # Create a new sample group
        new_group = SampleGroup(name)
        self.SGROUPS.append(new_group)
        print(f"Sample group '{name}' added.")
        self.AddSampleGroupNameEdit.clear()
        #Update UI stuff
        self.UpdateEverything()

    def CloneSampleGroup(self):
        """
        Clone the selected sgrouop.
        """
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if selected:
            selected_row = selected[0].row()
            original_group_name_item = self.ImporttabSampleGroupList.item(selected_row, 0)  # Column 0: Group Name

            if not original_group_name_item:
                print("No sample group selected.")
                return

            original_group_name = original_group_name_item.text()

            base_name = original_group_name.split('.')[0]
            suffix = 1
            new_group_name = f"{base_name}.{suffix}"

            # Ensure the new name is unique
            existing_names = [group.name for group in self.SGROUPS]
            while new_group_name in existing_names:
                suffix += 1
                new_group_name = f"{base_name}.{suffix}"

            # Clone the group
            for group in self.SGROUPS:
                if group.name == original_group_name:
                    cloned_group = SampleGroup(new_group_name, audio_files=group.audio_files)
                    self.SGROUPS.append(cloned_group)
                    print(f"Sample group '{original_group_name}' cloned as '{new_group_name}'.")
                    self.UpdateImportTab()
                    return

            print(f"Sample group '{original_group_name}' not found.")
        
        self.UpdateEverything()

    def AddAudioToSGroup(self):
        """
        Add selected audio files to the selected sample group.
        """
        selected_audio = self.AudioFilesList.selectedIndexes()
        selected_sgroup = self.ImporttabSampleGroupList.selectedIndexes()
        if not selected_audio or not selected_sgroup:
            print("No audio file or sample group selected.")
            return

        selected_sgroup = sorted(set(index.row() for index in selected_sgroup), reverse=True)
        selected_audio = sorted(set(index.row() for index in selected_audio), reverse=True)
        selected_sgroup = self.ImporttabSampleGroupList.item(selected_sgroup[0], 0)  # 0 = Group Name
        selected_sgroup = self.SGroupNameToObject(selected_sgroup.text())

        selected_audio = [self.AudioFilesList.item(index, 0) for index in selected_audio]  # 0 = Name
        audio_file_objs = self.AudioNamesToObjects([audio.text() for audio in selected_audio])

        print("Selected SGroup: ", selected_sgroup)
        print("Selected Audio: ", selected_audio)



        #get audio file objects
        # audio_names = []
        # audio_file_objs = []
        # for index in selected_audio:
        #     audio_file_item = self.AudioFilesList.item(index, 0)
        #     if audio_file_item:
        #         audio_file_name = audio_file_item.text()
        #         audio_names.append(audio_file_name)
        # for name in audio_names:
        #     for audio_file in self.audio_files:
        #         if audio_file.name == name:
        #             audio_file_objs.append(audio_file)
        #             break
        
        print("Audio file objects: ", audio_file_objs)

        for audio_file in audio_file_objs:
            if audio_file not in selected_sgroup.audio_files:
                selected_sgroup.audio_files.append(audio_file)
                print(f"Audio file '{audio_file.name}' added to sample group '{selected_sgroup.name}'.")
            else:
                print(f"Audio file '{audio_file.name}' already exists in sample group '{selected_sgroup.name}'.")

        self.UpdateImportTab()
        self.UpdateSliceTab()

    def AddNewSlice(self):
        # After method, update table according to new stuff

        self.UIDCounter += 1

        # Start Point
        if self.SampleCutpointInput.text() == '':
            return
        else:
            startpoint = int(self.SampleCutpointInput.text())

        # End Point
        if self.IsLengthCheckbox.isChecked():
            endpoint = int(self.SampleEndInput.value()) + startpoint
        else:
            endpoint = int(self.SampleEndInput.value())

        length = endpoint - startpoint

        if length <= 0:
            print("Invalid length.")
            return

        for slice in self.SLICES:
            if slice.start == startpoint and slice.end == endpoint:
                print("Slice already exists.")
                return

        selected_groups = self.SGroupNamesToObjects(self.SliceTabSelectedSGroups)
        if selected_groups is None:
            selected_groups = []

        # Create a new slice
        new_slice = Slice(startpoint, endpoint, selected_groups, False, None, None, self.UIDCounter)

        self.SLICES.append(new_slice)
        print("SLICES: ", self.SLICES)
        self.ResetSliceInputs()
        self.UpdateSliceTab()

    def ResetSliceInputs(self):
        self.SampleCutpointInput.setValue(0)
        self.SampleEndInput.setValue(0)

    def RemoveAudiofile(self):
        """
        Remove selected audio file from project.
        """
        selected = self.AudioFilesList.selectedIndexes()
        if selected:
            row = selected[0].row()
            if 0 <= row < len(self.AUDIOFILES):
                removed_file = self.AUDIOFILES.pop(row)
                print(f"Audio file '{removed_file.name}' removed from the project.")

        self.UpdateImportTab()

    def RemoveSampleGroup(self):
        """
        Delete the selected sample groups from the project.
        """
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if not selected:
            print("No sample group selected.")
            return

        rows_to_delete = sorted(set(index.row() for index in selected), reverse=True)

        for row in rows_to_delete:
            group_name_item = self.ImporttabSampleGroupList.item(row, 0)  # 0 = Group Name
            if group_name_item:
                group_name = group_name_item.text()
                for sgroup in self.SGROUPS:
                    if sgroup.name == group_name:
                        self.SGROUPS.remove(sgroup)
                        print(f"Sample group '{group_name}' deleted.")
                        break
                

        self.UpdateImportTab()

    def SelectAllSampleGroups(self):
        """
        Select all sample groups in the SampleGroupSelection table.
        """
        for i in range(self.SampleGroupSelection.rowCount()):
            checkbox_item = self.SampleGroupSelection.item(i, 2)    # 2 = Checkbox
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Checked)
        self.UpdateSelectedSGroup()

    def ClearAllSampleGroups(self):
        """
        Clear all sample groups in the SampleGroupSelection table.
        """
        for i in range(self.SampleGroupSelection.rowCount()):
            checkbox_item = self.SampleGroupSelection.item(i, 2)    # 2 = Checkbox
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        self.UpdateSelectedSGroup()

    def SGroupNamesToObjects(self, sgrouplist):
            """
            Return list of Sgroup objects from a list of names.

            :param sgrouplist: List of sgroup names.
            """

            if not sgrouplist:
                return None
            if sgrouplist == []:
                return None
            if not type(sgrouplist) == list:
                return
            if len(self.SGROUPS) == 0:
                return None
            
            out = []

            for name in sgrouplist:
                for sgroup in self.SGROUPS:
                    if sgroup.name == name:
                        out.append(sgroup)

            return out
            
    def SGroupNameToObject(self, sname):
            """
            Return list of Sgroup objects from a list of names.

            :param sgrouplist: List of sgroup names.
            """

            if not sname:
                return None
            if sname == "":
                return None
            if not type(sname) == str:
                return
            if len(self.SGROUPS) == 0:
                return None
            


            for sgroup in self.SGROUPS:
                if sgroup.name == sname:
                    out = sgroup

            return out

    def AudioNamesToObjects(self, audio_names):
        """
        Return list of AudioFile objects from a list of names.

        :param audio_names: List of audio file names.
        """

        if not audio_names:
            return None
        if audio_names == []:
            return None
        if not type(audio_names) == list:
            return
        if len(self.AUDIOFILES) == 0:
            return None
        
        out = []

        for name in audio_names:
            for audio_file in self.AUDIOFILES:
                if audio_file.name == name:
                    out.append(audio_file)

        return out

    def SortTabSGroupFilterUpdate(self):
        """
        Populate the SortTabSGroupfilter with sgroups.
        """
        self.SortTabSGroupfilter.clear() 
        self.SortTabSGroupfilter.addItem("SGroup Filter")  
        index = self.SortTabSGroupfilter.findText("SGroup Filter")
        if index != -1:
            self.SortTabSGroupfilter.model().item(index).setSizeHint(QtCore.QSize(0, 0))

        # Populate with sample group names
        for sgroup in self.SGROUPS:
            if sgroup:
                self.SortTabSGroupfilter.addItem(sgroup.name)

    def SortTabSliceListUpdate(self):
        """
        slices and stuff, click on them
        """
        selected_group_name = self.SortTabSGroupfilter.currentText()

        # Clear the SortTabSliceList
        self.SortTabSliceList.clearContents()
        self.SortTabSliceList.setRowCount(0)

        # If "SGroup Filter" is selected, show nothing
        if selected_group_name == "SGroup Filter":
            return

        sgroup = self.SGroupNameToObject(selected_group_name)

        if not sgroup:
            return  

        slices = []
        for i in range(self.Sample_Cut_Data_Table.rowCount()):
            item = self.Sample_Cut_Data_Table.item(i, 4)
            if item and sgroup.name in item.text():
                slices.append(self.SLICES[i])

        # Populate the SortTabSliceList with slices
        self.SortTabSliceList.setRowCount(len(slices))
        for i, slice in enumerate(slices):
            self.SortTabSliceList.setItem(i, 0, QTableWidgetItem(str(slice.UID))) # uid it is
            self.SortTabSliceList.setItem(i, 1, QTableWidgetItem("")) # 1 = note
            self.SortTabSliceList.setItem(i, 2, QTableWidgetItem(str(slice.start))) # 2 = Absolute Startpoint
            self.SortTabSliceList.setItem(i, 3, QTableWidgetItem(str(slice.end))) # 3 = Absolute Endpoint

    def downsample_for_plot(self, audio_data, max_points=4000, use_max=True):
        """
        Downsample audio data for plotting. Uses absolute maximum for each bin.
        """

        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)
        if len(audio_data) <= max_points:
            return audio_data
        factor = len(audio_data) // max_points
        trimmed = audio_data[:factor * max_points]
        # Use absolute maximum in each bin
        if use_max:
            return np.abs(trimmed).reshape(-1, factor).max(axis=1)
        else:
            return trimmed.reshape(-1, factor).mean(axis=1)

    def on_waveform_view_changed(self, object, pos_tuple):
        # Only load and plot this segment

        if object.objectName() == "SliceWaveformVisu":
            is_slicewf = True
        else:
            is_slicewf = False

        graph_start, graph_end = pos_tuple
        print(f"Waveform view changed: start={graph_start}, end={graph_end}")

        # Convert graph_start and graph_end (graph coordinates) to integer sample indices
        # Here, 0 is sample 0 and 1 is the length of the audio file (normalized coordinates)
        audio_file = self.SliceAudioFileSelect.currentText()
        if not audio_file:
            print("No audio file selected for waveform view.")
            return
        audio_obj = self.AudioNamesToObjects([audio_file])[0]
        if not audio_obj:
            print(f"Audio object for '{audio_file}' not found.")
            return

        audio_length = audio_obj.length if hasattr(audio_obj, 'length') else 0
        start_sample = int(np.clip(round(graph_start * audio_length), 0, audio_length))
        end_sample = int(np.clip(round(graph_end * audio_length), 0, audio_length))

        audio_file = self.SliceAudioFileSelect.currentText()
        if not audio_file:
            print("No audio file selected for waveform view.")
            return
        audio_obj = self.AudioNamesToObjects([audio_file])[0]
        if not audio_obj:
            print(f"Audio object for '{audio_file}' not found.")
            return

        audio_data = self.GetAudioData(audio_obj, start_sample, end_sample)
        audio_data = self.downsample_for_plot(audio_data, max_points=2000, use_max=is_slicewf)
        self.WaveformPlot(audio_data, self.SliceWaveformVisu)

    def WaveformPlot(self, audio_data, graphitem, max_points=2000):
        """
        Plot the waveform of the audio data, downsampling if necessary.
        """

        isslicewf = False

        if audio_data is None or len(audio_data) == 0:
            print("No audio data to plot.")
            graphitem.clear()
            return

        # Downsample for display
        audio_data = self.downsample_for_plot(audio_data, max_points=max_points, use_max=isslicewf)

        start_time = 0
        end_time = len(audio_data)

        try:
            graphitem.clear()
            graphitem.setXRange(start_time, end_time, padding=0)
            if isslicewf:
                graphitem.setYRange(0, 1, padding=0)
            else:
                graphitem.setYRange(-1, 1, padding=0)
            time_axis = np.linspace(start_time, end_time, num=len(audio_data))
            maax = max([max(audio_data), abs(min(audio_data))])
            if maax == 0:
                maax = 1
            audio_data = audio_data / maax  # Normalize
            graphitem.plot(time_axis, audio_data, pen="blue")
        except Exception as e:
            print(f"Error plotting audio file: {e}")
            graphitem.clear()

    def SortTabAudioAnalysisUpdate(self):
        """
        Analyze the selected slice and update the audio preview.
        """

        print(self.SLICES)

        selected_slice = self.SortTabSliceList.selectedIndexes()
        if not selected_slice:
            print("No slice selected.")
            return

        selected_row = selected_slice[0].row()
        uid_text = self.SortTabSliceList.item(selected_row, 0).text()
        try:
            uid = int(uid_text)
        except (TypeError, ValueError):
            print(f"Invalid UID value: {uid_text}")
            return
        SliceObject = self.SliceUIDToObject(uid)
        print("Selected Slice: ", SliceObject)
        if not SliceObject:
            print("No slice object found.")
            return
        
        start = SliceObject.start
        end = SliceObject.end

        Slice_Audio = self.GetAudioData(SliceObject, start, end)

        if Slice_Audio is None:
            print("Error getting audio data.  -sorttab-")
            return
        
        Names = []
        for tuple in Slice_Audio:
            Names.append(tuple[0])

        self.SortPreviewAudioSelect.clear()
        for name in Names:
            self.SortPreviewAudioSelect.addItem(name)

        self.SortAudioWaveformUpdate()

        

                                                         # REDO ALL AUDIO LOADING THINGS

    def SortAudioWaveformUpdate(self):   
        selected_slice = self.SortTabSliceList.selectedIndexes()
        if not selected_slice:
            print("No slice selected.")
            return
        selected_row = selected_slice[0].row()
        uid_text = self.SortTabSliceList.item(selected_row, 0).text()
        try:
            uid = int(uid_text)
        except (TypeError, ValueError):
            print(f"Invalid UID value: {uid_text}")
            return
        SliceObject = self.SliceUIDToObject(uid)
        print("Selected Slice: ", SliceObject)
        if not SliceObject:
            print("No slice object found.")
            return
        
        start = SliceObject.start
        end = SliceObject.end

        Slice_Audio = self.GetAudioData(SliceObject, start, end)

        if Slice_Audio is None:
            print("Error getting audio data. -sortwaveformupdate-")
            return

        #get selected audio file
        selected_audio = self.SortPreviewAudioSelect.currentText()

        #get audio data from selected name

        audio_data = None
        for audio_file in Slice_Audio:
            if audio_file[0] == selected_audio:
                audio_data = audio_file[1]
                break

        #apply the slice range to the audio data
        start = SliceObject.start
        end = SliceObject.end

        if audio_data is None:
            print("Error loading audio file -sortaudiowaveformupdate2-.")
            return

        self.WaveformPlot(audio_data, self.WaveformVisu)

        sr = SliceObject.sample_rate if hasattr(SliceObject, 'sample_rate') else 44100
        # get note frequency
        diff, note = PitchDetection(audio_data, sr)
        print(f"Detected note: {note}, diff: {diff:.2f} cts")
        if note is not None:
            MidiNote = MidiNoteToName(note)

            self.NoteLabel.setText(f"Note: {MidiNote}")
            print(f"Detected note: {MidiNote} +-{diff:.2f} cts")


    def SliceAudioWaveformUpdate(self):   
        selected_audio = self.SliceAudioFileSelect.currentText()
        if not selected_audio:
            print("No audio file selected.")
            return
        
        audio_obj = self.AudioNamesToObjects([selected_audio])[0]
        if not audio_obj:
            print(f"Audio object for '{selected_audio}' not found.")
            return

        start = 0
        end = audio_obj.length

        AudioData = self.GetAudioData(audio_obj, start, end)

        if AudioData is None or len(AudioData) == 0:
            print("Error getting audio data. -slicewaveformupdate-")
            return

        AudioData = AudioData[0][1] 

        if AudioData is None:
            print("Audio data for selected file not found in cache.")
            return

        self.WaveformPlot(AudioData, self.SliceWaveformVisu)
        AudioData = 0



    def GetAudioData(self, obj, start=None, end=None):
        '''
        Get cached audio data for the selected slice or audio file.
        Accepts either a Slice, SampleGroup, or AudioFile.
        Returns a list of [name, audio_data] pairs.
        '''
        print(f"begin {obj}")
        use_whole_file = False
        if end == 0:
            use_whole_file = True

        # Handle AudioFile directly
        if isinstance(obj, AudioFile):
            
            length = obj.length
            start = start if start is not None else 0
            end = end if end is not None else length
            if end == start:
                use_whole_file = True

            if not os.path.isfile(obj.file_path):
                print(f"File not found: {obj.file_path}")
                return []
            try:
                with PyWave.open(obj.file_path, 'r') as wav_file:
                    if end == 0 or end > wav_file.samples:
                        audio_end = wav_file.samples
                    else:
                        audio_end = end
                    if use_whole_file:
                        start = 0
                        audio_end = wav_file.samples
                        end = wav_file.samples

                    audio_data = wav_file.read_samples(audio_end)
                    format = FormatIDToName(wav_file.format)
                    audio_data = self.convert_to_int16(audio_data, wav_file.bits_per_sample, format)
                    if use_whole_file:
                        audio_data
                    else:
                        audio_data = audio_data[start:end]
                    return [[obj.name, audio_data]]
            except Exception as e:
                print(f"Error loading audio file {obj.name}: {e} -getaudiodata-")
                return []

        # Handle SampleGroup
        if isinstance(obj, SampleGroup):
            obj = Slice(0, 0, [obj], False, None, None, None)

        # Handle Slice
        if not isinstance(obj, Slice):
            print(f"Invalid object for GetAudioData: {type(obj)}")
            return []

        # Use slice's start/end if not provided
        start = start if start is not None else obj.start
        end = end if end is not None else obj.end

        out = []

        if self.CacheType == "LoadAllFromDrive":
            for sgroup in obj.sample_groups:
                for audio_file in sgroup.audio_files:
                    name = audio_file.name
                    if not os.path.isfile(audio_file.file_path):
                        print(f"File not found: {audio_file.file_path}")
                        continue
                    try:
                        with PyWave.open(audio_file.file_path, 'r') as wav_file:
                            if end == 0 or end > wav_file.samples:
                                audio_end = wav_file.samples
                            else:
                                audio_end = end
                            audio_data = wav_file.read_samples(audio_end)
                            format = FormatIDToName(wav_file.format)
                            audio_data = self.convert_to_int16(audio_data, wav_file.bits_per_sample, format)
                            if use_whole_file:
                                audio_data
                            else:
                                audio_data = audio_data[start:end]
                            out.append([name, audio_data])
                    except Exception as e:
                        print(f"Error loading audio file {name}: {e}")
        else:
            self.CacheSliceAudioData(obj)
            for sgroup in obj.sample_groups:
                for audio_file in sgroup.audio_files:
                    name = audio_file.name
                    for cached_audio in self.CACHEDAUDIOFILES:
                        if cached_audio[0] == name:
                            if use_whole_file:
                                start = 0
                                end = len(cached_audio[1])
                            cached_audio_data = cached_audio[1][start:end]
                            out.append([name, cached_audio_data])

        return out

    def CheckSliceAudioCache(self, slice):
        """
        Check if audio data for the selected slice is already cached.
        Return audio names of uncached audio
        """
        if type(slice) != Slice:
            print("Invalid slice object. -checkslice-")
            return

        out = []

        for sgroup in slice.sample_groups:
            for audio_file in sgroup.audio_files:
                name = audio_file.name
                cached = False
                for cached_audio in self.CACHEDAUDIOFILES:
                    if cached_audio[0] == name:
                        cached = True
                        break
                if not cached:
                    out.append(audio_file)

        return out

    def CacheSliceAudioData(self, slice):
        """
        Cache audio data for the selected slice.
        """

        if self.CacheType == "LoadAllFromDrive":
            return

        if type(slice) != Slice:
            print("Invalid slice object. -cacheslice-")
            return
        
        to_cache = self.CheckSliceAudioCache(slice)
        if not to_cache:
            print("All audio files for this slice are already cached.")
            return

        #Cache audio files
        for audio_file in to_cache:
            self.CacheAudioFile(audio_file)  

    def convert_to_int16(self, raw_data, bits_per_sample, sample_format='PCM'):
        """
        Convert raw audio bytes of any supported bit depth/format to 16-bit PCM.

        Args:
            raw_data (bytes): The raw audio byte stream.
            bits_per_sample (int): Bit depth of the input data (8, 16, 24, 32, 64).
            sample_format (str): 'PCM' or 'FLOAT'.

        Returns:
            np.ndarray: 16-bit integer numpy array.
        """
        if sample_format == 'WAVE_FORMAT_IEEE_FLOAT':
            # FLOAT input: determine dtype
            if bits_per_sample == 32:
                dtype = np.float32
            elif bits_per_sample == 64:
                dtype = np.float64
            else:
                raise ValueError("Unsupported float bit depth")

            float_data = np.frombuffer(raw_data, dtype=dtype)
            float_data = np.clip(float_data, -1.0, 1.0)  # clip to avoid overflow
            return (float_data * 32767).astype(np.int16)

        elif sample_format == 'WAVE_FORMAT_PCM':
            if bits_per_sample == 8:
                # Unsigned 8-bit PCM
                data = np.frombuffer(raw_data, dtype=np.uint8)
                return ((data.astype(np.int16) - 128) << 8)  # Center and scale
            elif bits_per_sample == 16:
                return np.frombuffer(raw_data, dtype=np.int16)
            elif bits_per_sample == 24:
                # 24-bit PCM is unpacked manually
                samples = np.frombuffer(raw_data, dtype=np.uint8)
                samples = samples.reshape(-1, 3)
                # Combine bytes (little endian): pad with sign byte
                int32 = (samples[:, 0].astype(np.int32) |
                     (samples[:, 1].astype(np.int32) << 8) |
                     (samples[:, 2].astype(np.int32) << 16))
                # Sign extension for 24-bit
                int32 = np.where(int32 & 0x800000, int32 | ~0xFFFFFF, int32)
                return (int32 >> 8).astype(np.int16)
            elif bits_per_sample == 32:
                # Convert 32-bit int to 16-bit
                data = np.frombuffer(raw_data, dtype=np.int32)
                return (data >> 16).astype(np.int16)
            else:
                raise ValueError("Unsupported PCM bit depth")
        else:
            raise ValueError("Unsupported sample format: must be 'PCM' or 'FLOAT'")

    def int16_to_list(self, int16_array):
        """
        Convert a NumPy array of int16 samples to a regular Python list of ints.

        Args:
            int16_array (np.ndarray): Numpy array with dtype=int16.

        Returns:
            List[int]: A list of Python integers.
        """
        if int16_array.dtype != np.int16:
            raise ValueError("Input array must have dtype int16")
        
        return int16_array.tolist()

    def CacheAudioFile(self, audio_file):
        """
        Cache audio data for the selected audio file.
        """
        if self.CacheType == "LoadAllFromDrive":
            return
        print("Caching audio file...")
        if type(audio_file) != AudioFile:
            print("Invalid audio file object.")
            return
        print(f"Loading audio file {audio_file.name}")
        file_path = audio_file.file_path

        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return

        

        try:
            with PyWave.open(file_path, 'r') as wav_file:

                # Read the audio data
                audio_data = wav_file.read_samples(wav_file.samples)
                format = wav_file.format
                if format == 1: format = "WAVE_FORMAT_PCM"
                elif format == 2: format = "WAVE_FORMAT_IEEE_FLOAT"
                else: format = "Unknown"
                audio_data = self.convert_to_int16(audio_data, wav_file.bits_per_sample, format)
                #audio_data = self.int16_to_list(audio_data)
                #audio_data = np.frombuffer(audio_data, dtype=np.int16)
                
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return

        # Cache the audio data
        self.CACHEDAUDIOFILES.append((audio_file.name, audio_data))
        audio_data = None  # Clear the variable to free memory
        print(f"Audio file {audio_file.name} cached successfully.")

    def SliceUIDToObject(self, uid):
        """
        Return the slice object corresponding to the given UID.
        """
        for slice in self.SLICES:
            if slice.UID == uid:
                return slice
        return None

    def DisplaySettings(self):
        """
        Display the settings dialog.
        """
        print("Displaying settings dialog.")
        self.settings_window = SettingsWindow(main_ui=self)

        self.settings_window.setWindowModality(Qt.ApplicationModal)
        if getattr(sys, 'frozen', False):
            icon = QIcon(os.path.join(sys._MEIPASS, "icon.ico"))
        else:
            icon = QIcon("icon.ico")
        self.settings_window.setWindowTitle("Settings - BaSlicer")
        self.settings_window.setWindowIcon(icon)
        self.settings_window.show()
        print("MEEP!")

    def MainApplySettings(self):
        """
        Apply the settings from the settings dialog.
        """
        print("Applying settings from the settings dialog.")
        # Get settings from QSettings
        settings = QSettings("Vaven", "BaSlicer")
        settings.beginGroup("Memory")
        self.CacheType = settings.value("CacheType", "Memory")
        self.AudioCacheSize = settings.value("AudioCacheSize", 100)  # Default to 100 MB
        settings.endGroup()
        settings.beginGroup("Audio")
        self.AudioDevice = settings.value("OutputDevice", "Default")
        settings.endGroup()
        settings.beginGroup("General")
        theme = settings.value("Theme", "light")
        qdarktheme.setup_theme(theme)
        settings.endGroup()

    def SaveWindowSize(self):
        """
        Save the current window size to QSettings.
        """
        settings = QSettings("Vaven", "BaSlicer")
        settings.setValue("Window/Size", self.size())
        settings.setValue("Window/Position", self.pos())
        print("Window size and position saved.")

    def LoadWindowSize(self):
        """
        Load the window size and position from QSettings.
        """
        settings = QSettings("Vaven", "BaSlicer")
        size = settings.value("Window/Size", QSize(800, 600))
        position = settings.value("Window/Position", QPoint(100, 100))
        # Use the main window if available
        if hasattr(self, 'main_window') and self.main_window is not None:
            self.main_window.resize(size)
            self.main_window.move(position)
        elif hasattr(self, 'parent') and self.parent() is not None:
            self.parent().resize(size)
            self.parent().move(position)
        print("Window size and position loaded.")

    def UpdateEverything(self):
        """
        Update all UI elements in the main window.
        """
        self.UpdateImportTab()
        self.UpdateSliceTab()
        self.UpdateSortTab()

    def UpdateSliceTab(self):
        """
        Update all UI elements in slice tab.
        """

        self.Saved = False

        # SGroup selection table
        self.SampleGroupSelection.setRowCount(len(self.SGROUPS))
        for i, sgroup in enumerate(self.SGROUPS):
            self.SampleGroupSelection.setItem(i, 0, QTableWidgetItem(sgroup.name)) # 0 = Name
            self.SampleGroupSelection.setItem(i, 1, QTableWidgetItem("")) # 1 = Unused
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            self.SampleGroupSelection.setItem(i, 2, checkbox_item) # 2 = Checkbox
            self.SampleGroupSelection.setItem(i, 3, QTableWidgetItem("")) # 3 = Unused
        
        # Sample cut data table
        self.Sample_Cut_Data_Table.setRowCount(len(self.SLICES))
        for i, slice in enumerate(self.SLICES):
            self.Sample_Cut_Data_Table.setItem(i, 0, QTableWidgetItem(str(i))) # 0 = Unused
            self.Sample_Cut_Data_Table.setItem(i, 1, QTableWidgetItem(str(slice.start))) # 1 = Absolute Startpoint
            self.Sample_Cut_Data_Table.setItem(i, 2, QTableWidgetItem(str(slice.end))) # 2 = Absolute Endpoint
            self.Sample_Cut_Data_Table.setItem(i, 3, QTableWidgetItem(str(slice.end-slice.start))) # 3 = Length
            sliceSGroups = slice.sample_groups
            sliceSGroups = [sgroup.name for sgroup in sliceSGroups]
            self.Sample_Cut_Data_Table.setItem(i, 4, QTableWidgetItem(", ".join(sliceSGroups))) # 4 = SGroups

        # Keep selected SGroups
        for selectedgroup in self.SliceTabSelectedSGroups:
            for i in range(self.SampleGroupSelection.rowCount()):
                checkbox_item = self.SampleGroupSelection.item(i, 2)
                name = self.SampleGroupSelection.item(i, 0)  # 0 = Name
                if checkbox_item and name and name.text() == selectedgroup:
                    checkbox_item.setCheckState(Qt.CheckState.Checked)
                    break

    def PopulateSliceTabAudioPreviewBox(self):
        """
        Populate the audio preview box in the slice tab.
        """
        
        self.SliceAudioFileSelect.clear()
        selected_sgroups = self.SliceTabSelectedSGroups
        if not selected_sgroups:
            print("No sample groups selected.")
            return
        names = []
        for sgroup_name in selected_sgroups:
            sgroup = self.SGroupNameToObject(sgroup_name)
            if not sgroup:
                print(f"Sample group '{sgroup_name}' not found.")
                continue
            for audio_file in sgroup.audio_files:
                audio_item = audio_file.name
                print(f"Adding audio file '{audio_file.name}' from sample group '{sgroup_name}' to SliceAudioFileSelect.")
                names.append(audio_item)

        names = list(dict.fromkeys(names))

        self.SliceAudioFileSelect.addItems(names)

    def UpdateSelectedSGroup(self):
        '''
        Get selected SGroups from Slice tab.
        '''

        self.Saved = False

        if len(self.SGROUPS) == 0:
            return

        checked_groups = []
        for i in range(self.SampleGroupSelection.rowCount()):
            checkbox_item = self.SampleGroupSelection.item(i, 2)    # 2 = Checkbox
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                name = self.SampleGroupSelection.item(i, 0)  # 0 = Name
                if name:
                    checked_groups.append(name.text())

        self.SliceTabSelectedSGroups = checked_groups

        print("Selected SGroups: ", self.SliceTabSelectedSGroups)

    def UpdateImportTab(self):
        """
        Update all UI elements in the import tab.
        """

        self.Saved = False

        selected_sgroups = self.ImporttabSampleGroupList.selectedIndexes()
        selected_audio = self.AudioFilesList.selectedIndexes()

        self.ImporttabSampleGroupList.setRowCount(0)
        self.AudioFilesList.setRowCount(0)

        # SGroups
        if not self.SGROUPS:
            print("No sample groups available.")
            self.ImporttabSampleGroupList.setRowCount(0)
        else:
            self.ImporttabSampleGroupList.setRowCount(len(self.SGROUPS))
            for i, sgroup in enumerate(self.SGROUPS):
                if sgroup:
                    self.ImporttabSampleGroupList.setItem(i, 0, QTableWidgetItem(sgroup.name))  #  0: Name
                    self.ImporttabSampleGroupList.setItem(i, 1, QTableWidgetItem(""))  #  1: Unused
                    self.ImporttabSampleGroupList.setItem(i, 2, QTableWidgetItem(""))  #  2: Unused
                    SGroupAudioFiles = ", ".join([audio_file.name for audio_file in sgroup.audio_files])
                    self.ImporttabSampleGroupList.setItem(i, 3, QTableWidgetItem(SGroupAudioFiles))  #  3: Audio Files

        # Audio Files
        if not self.AUDIOFILES:
            print("No audio files available.")
            self.AudioFilesList.setRowCount(0)
        else:
            self.AudioFilesList.setRowCount(len(self.AUDIOFILES))
            for i, audio_file in enumerate(self.AUDIOFILES):
                if audio_file:
                    self.AudioFilesList.setItem(i, 0, QTableWidgetItem(audio_file.name))  #  0: Name
                    self.AudioFilesList.setItem(i, 1, QTableWidgetItem(audio_file.file_path))  #  1: File Path
                    self.AudioFilesList.setItem(i, 2, QTableWidgetItem(str(audio_file.channels)))  #  2: Channels
                    self.AudioFilesList.setItem(i, 3, QTableWidgetItem(str(audio_file.sample_rate)))  #  3: Sample Rate
                    self.AudioFilesList.setItem(i, 4, QTableWidgetItem(str(audio_file.bit_depth)))  #  4: Bit Depth
                    self.AudioFilesList.setItem(i, 5, QTableWidgetItem(str(audio_file.length)))  #  5: Length
                    self.AudioFilesList.setItem(i, 6, QTableWidgetItem(""))  #  6: Unused

        # restore selection
        self.ImporttabSampleGroupList.setCurrentItem(self.ImporttabSampleGroupList.item(selected_sgroups[0].row(), 0)) if selected_sgroups else None
        self.AudioFilesList.setCurrentItem(self.AudioFilesList.item(selected_audio[0].row(), 0)) if selected_audio else None

        self.UpdateImportTabSGroupContentPreview()

        print("Import tab updated successfully.")
        
    def UpdateImportTabSGroupContentPreview(self):
        """
        Update the content preview of the selected sample group in the import tab.
        """

        self.Saved = False

        selectedsgroup = self.ImporttabSampleGroupList.selectedIndexes()

        if selectedsgroup:
            selectedsgroup = selectedsgroup[0].row()
            selectedsgroup = self.ImporttabSampleGroupList.item(selectedsgroup, 0).text()
        else:
            return

        SGroupItem = self.SGroupNameToObject(selectedsgroup)
        print("SGroupItem: ", SGroupItem)

        self.SampleGroupContentsPreview.setRowCount(0)  # Clear previous contents

        for i, audio_file in enumerate(SGroupItem.audio_files):
            if audio_file:
                self.SampleGroupContentsPreview.setRowCount(len(SGroupItem.audio_files))
                self.SampleGroupContentsPreview.setItem(i, 0, QTableWidgetItem(audio_file.name))  # 0 = Name

    def UpdateSortTab(self):
        """
        Update all UI elements in the sort tab.
        """



        self.Saved = False

        # SGroup selection table
        self.SortTabSGroupfilter.clear()
        
        self.SortTabSGroupFilterUpdate()
def GetWavInfo(file_path: str) -> tuple[int, int, int, int]:
    """
    Extracts WAV file attributes using the PyWave module.

    :param file_path: Path to the WAV file.
    :return: A tuple containing (num_channels, sample_rate, bit_depth, num_frames).
    """
    try:
        with PyWave.open(file_path, 'r') as wav_file:
            num_channels = wav_file.channels
            sample_rate = wav_file.frequency
            bit_depth = wav_file.bits_per_sample
            # num_frames = wav_file.num_frames
            num_frames = 0
            print(f"Channels: {num_channels}, Sample Rate: {sample_rate}, Bit Depth: {bit_depth}, Frames: {num_frames}")
            return num_channels, sample_rate, bit_depth, num_frames
    except Exception as e:
        print(f"Error reading WAV file: {e}")
        return -1, -1, -1, -1



def FastResample(samples, original_rate, target_rate):
    """
    Fast and low-quality resampling
    
    Args:
        samples (list or np.array): Input samples.
        original_rate (int): Original sample rate.
        target_rate (int): Target sample rate.

    Returns:
        np.array: Resampled audio samples.
    """
    if not isinstance(samples, (list, np.ndarray)):
        raise ValueError("Samples must be a list or numpy array.")

    if original_rate <= 0 or target_rate <= 0:
        raise ValueError("Sample rates must be positive integers.")

    if original_rate == target_rate:
        return np.asarray(samples)

    samples = np.asarray(samples)
    ratio = target_rate / original_rate
    n_target_samples = int(len(samples) * ratio)

    indices = np.linspace(0, len(samples) - 1, n_target_samples).astype(int)
    resampled = samples[indices]

    return resampled

def FormatIDToName(format_id):
    """
    Convert a format ID to a human-readable name.
    
    Args:
        format_id (int): Format ID.
    
    Returns:
        str: Human-readable format name.
    """
    if format_id == 1:
        return "WAVE_FORMAT_PCM"
    elif format_id == 2:
        return "WAVE_FORMAT_ADPCM"
    elif format_id == 3:
        return "WAVE_FORMAT_IEEE_FLOAT"
    else:
        return "Unknown Format"

def PitchDetection(samples, samplerate):
    """
    Detects the fundamental frequency (pitch) of the given audio samples using scipy.signal.correlate,
    and returns the pitch difference in cents from the closest note.

    Args:
        samples (np.array): Audio samples (mono, normalized).
        samplerate (int): Sample rate of the audio.

    Returns:
        tuple: Detected pitch difference in cents, and the corresponding midi note.
    """
    if not isinstance(samples, np.ndarray):
        raise ValueError("Samples must be a numpy array.")
    
    if len(samples) <= 2:
        return None, None
    
    if samplerate <= 0:
        raise ValueError("Samplerate must be a positive integer.")
    
    samples = samples - np.mean(samples) #DC Offset
    samples = samples / np.max(np.abs(samples))  # Normalize to -1 to 1

    corr = correlate(samples, samples, mode='full')
    corr = corr[len(corr)//2:]  # Keep only second half (non-negative lags)

    d = np.diff(corr)
    start = np.nonzero(d > 0)[0]
    if len(start) == 0:
        return None, None 
    start = start[0]

    peak = np.argmax(corr[start:]) + start
    period = peak

    if period == 0:
        return None, None

    frequency = samplerate / period

    # Convert frequency to nearest MIDI note
    midi_note = 69 + 12 * np.log2(frequency / 440.0)
    midi_note = round(midi_note)

    note_freq = 440.0 * (2 ** ((midi_note - 69) / 12.0))

    cents_difference = 1200 * np.log2(frequency / note_freq)

    return cents_difference, midi_note

def MidiNoteToName(midi_note):
    """
    Convert a MIDI note number to a note name

    Args:
        midi_note (int): MIDI note number (0-127).

    Returns:
        str: Note name with octave (e.g., "C4", "A#3").
    """
    if midi_note < 0 or midi_note > 127:
        return "Invalid"
    midi_note = int(midi_note)
    note_index = midi_note % 12
    octave = (midi_note // 12) - 1
    note_name = NOTE_NAMES[note_index]
    return f"{note_name}{octave}"
