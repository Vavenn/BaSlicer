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
    QMenuBar, QMenu, QWidget, QMessageBox
)
from PySide6 import QtCore
from PySide6.QtMultimedia import QAudioOutput, QAudioFormat
from PySide6.QtCore import QRect, QSettings, QMetaObject, QCoreApplication, Qt
from PySide6.QtGui import QCloseEvent, QAction, QFont
import numpy as np
from scipy.signal import correlate
import pyqtgraph as pg
import sounddevice as sd
import contextlib

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
            
class Ui_MainWindow(object):
    def __init__(self):
        self.Saved = False
        
        self.VERSION = "0.2.0"
        self.AUDIOFILES = []
        self.SGROUPS = []
        self.SLICES = []

        self.CACHEDAUDIOFILES = [] # tuples of slice UID, audio name, audio data

        self.SliceTabSelectedSGroups = []

        self.UIDCounter = 0

    def setupUi(self, MainWindow):
        DEV = True
        self.audio_output = QAudioOutput()  # Initialize audio_output
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1227, 604)
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

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.MainTabs = QTabWidget(self.centralwidget)
        #self.MainTabs.currentChanged.connect(self.updatetabs)

        self.MainTabs.setObjectName(u"MainTabs")
        self.MainTabs.setGeometry(QRect(-4, -1, 1251, 571))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.MainTabs.sizePolicy().hasHeightForWidth())
        self.MainTabs.setSizePolicy(sizePolicy)
 
            #           IMPORT TAB

        self.Import = QWidget()
        self.Import.setObjectName(u"Import")

        self.SampleGroupConfig = QGroupBox(self.Import)
        self.SampleGroupConfig.setObjectName(u"SampleGroupConfig")
        self.SampleGroupConfig.setGeometry(QRect(650, 20, 441, 511))

        self.ImporttabSampleGroupList = QTableWidget(self.SampleGroupConfig)
        self.ImporttabSampleGroupList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ImporttabSampleGroupList.setObjectName(u"ImporttabSampleGroupList")
        self.ImporttabSampleGroupList.setGeometry(QRect(10, 20, 191, 481))
        font = self.ImporttabSampleGroupList.font()
        font.setPointSize(17)
        font.setBold(False)
        self.ImporttabSampleGroupList.setFont(font)
        self.ImporttabSampleGroupList.setColumnCount(3)
        self.ImporttabSampleGroupList.setColumnWidth(0, 190)
        if not DEV:
            self.ImporttabSampleGroupList.hideColumn(1)
            self.ImporttabSampleGroupList.hideColumn(2)
        self.ImporttabSampleGroupList.verticalHeader().setVisible(False)
        self.ImporttabSampleGroupList.horizontalHeader().setVisible(False)
        self.ImporttabSampleGroupList.setSelectionBehavior(QTableWidget.SelectRows)
        self.ImporttabSampleGroupList.setSelectionMode(QTableWidget.SingleSelection)
        self.ImporttabSampleGroupList.clicked.connect(self.UpdateImportTabSGroupContentPreview)

        self.AddSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        self.AddSampleGroupBox.setObjectName(u"AddSampleGroupBox")
        self.AddSampleGroupBox.setGeometry(QRect(210, 10, 221, 51))

        self.AddSampleGroupNameEdit = QLineEdit(self.AddSampleGroupBox)
        self.AddSampleGroupNameEdit.setObjectName(u"AddSampleGroupNameEdit")
        self.AddSampleGroupNameEdit.setGeometry(QRect(10, 20, 171, 22))

        self.AddSampleGroupconfirm = QPushButton(self.AddSampleGroupBox)
        self.AddSampleGroupconfirm.setObjectName(u"AddSampleGroupconfirm")
        self.AddSampleGroupconfirm.setGeometry(QRect(190, 20, 21, 24))
        self.AddSampleGroupconfirm.clicked.connect(self.AddNewSGroup)

        self.RenameSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        self.RenameSampleGroupBox.setObjectName(u"RenameSampleGroupBox")
        self.RenameSampleGroupBox.setGeometry(QRect(210, 60, 221, 51))

        self.RenameSampleGroupEdit = QLineEdit(self.RenameSampleGroupBox)
        self.RenameSampleGroupEdit.setObjectName(u"RenameSampleGroupEdit")
        self.RenameSampleGroupEdit.setGeometry(QRect(10, 20, 171, 22))

        self.RenameSampleGroupConfig = QPushButton(self.RenameSampleGroupBox)
        self.RenameSampleGroupConfig.setObjectName(u"RenameSampleGroupConfig")
        self.RenameSampleGroupConfig.setGeometry(QRect(190, 20, 21, 24))
        #self.RenameSampleGroupConfig.clicked.connect(self.rename_sample_group)

        self.SampleGroupMove = QGroupBox(self.SampleGroupConfig)
        self.SampleGroupMove.setObjectName(u"SampleGroupMove")
        self.SampleGroupMove.setGeometry(QRect(240, 110, 71, 91))

        self.SampleGroupMoveUp = QPushButton(self.SampleGroupMove)
        self.SampleGroupMoveUp.setObjectName(u"SampleGroupMoveUp")
        self.SampleGroupMoveUp.setGeometry(QRect(10, 20, 51, 24))
        #self.SampleGroupMoveUp.clicked.connect(self.sgroupmoveup)

        self.SampleGroupMoveDown = QPushButton(self.SampleGroupMove)
        self.SampleGroupMoveDown.setObjectName(u"SampleGroupMoveDown")
        self.SampleGroupMoveDown.setGeometry(QRect(10, 50, 51, 24))
        #self.SampleGroupMoveDown.clicked.connect(self.sgroupmovedown)

        self.SampleGroupEdit = QGroupBox(self.SampleGroupConfig)
        self.SampleGroupEdit.setObjectName(u"SampleGroupEdit")
        self.SampleGroupEdit.setGeometry(QRect(330, 110, 71, 91))

        self.SampleGroupRemove = QPushButton(self.SampleGroupEdit)
        self.SampleGroupRemove.setObjectName(u"SampleGroupRemove")
        self.SampleGroupRemove.setGeometry(QRect(10, 20, 51, 24))
        self.SampleGroupRemove.clicked.connect(self.RemoveSampleGroup)

        self.SampleGroupClone = QPushButton(self.SampleGroupEdit)
        self.SampleGroupClone.setObjectName(u"SampleGroupClone")
        self.SampleGroupClone.setGeometry(QRect(10, 50, 51, 24))
        self.SampleGroupClone.clicked.connect(self.CloneSampleGroup)

        self.SampleGroupContentsPreview = QTableWidget(self.SampleGroupConfig)
        self.SampleGroupContentsPreview.setObjectName(u"SampleGroupContentsPreview")
        self.SampleGroupContentsPreview.setGeometry(QRect(210, 291, 221, 211))
        self.SampleGroupContentsPreview.setColumnCount(1)
        self.SampleGroupContentsPreview.setColumnWidth(0,221)
        self.SampleGroupContentsPreview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.SampleGroupContentsPreview.verticalHeader().setVisible(False)
        self.SampleGroupContentsPreview.horizontalHeader().setVisible(False)

        self.SampleGroupContentsLabel = QLabel(self.SampleGroupConfig)
        self.SampleGroupContentsLabel.setObjectName(u"SampleGroupContentsLabel")
        self.SampleGroupContentsLabel.setGeometry(QRect(210, 270, 49, 16))

        self.AddAudioToSGroupButton = QPushButton(self.SampleGroupConfig)
        self.AddAudioToSGroupButton.setObjectName(u"AddAudioToSGroup")
        self.AddAudioToSGroupButton.setGeometry(QRect(210, 210, 221, 24))
        self.AddAudioToSGroupButton.clicked.connect(self.AddAudioToSGroup)

        self.RemoveAudioGromSGroup = QPushButton(self.SampleGroupConfig)
        self.RemoveAudioGromSGroup.setObjectName(u"RemoveAudioGromSGroup")
        self.RemoveAudioGromSGroup.setGeometry(QRect(210, 240, 221, 24))

        self.AudioFilesListGroup = QGroupBox(self.Import)
        self.AudioFilesListGroup.setObjectName(u"AudioFilesListGroup")
        self.AudioFilesListGroup.setGeometry(QRect(10, 160, 631, 371))

        self.AudioFilesList = QTableWidget(self.AudioFilesListGroup)
        self.AudioFilesList.verticalHeader().setVisible(False)
        self.AudioFilesList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.AudioFilesList.setObjectName(u"AudioFilesList")
        self.AudioFilesList.setGeometry(QRect(10, 20, 611, 341))
        self.AudioFilesList.setColumnCount(7)
        if not DEV:
            self.AudioFilesList.hideColumn(6)
        self.AudioFilesList.setSelectionBehavior(QTableWidget.SelectRows)
        self.AudioFilesList.setHorizontalHeaderLabels(("Name", "File", "Channels", "Sample Rate", "Bit Depth", "Lenght", "id"))
        AudioFilesTableWidths = ((0,80),(1,284),(2,55),(3,75),(4,55),(5,60),(6,30))
        for i in AudioFilesTableWidths:
            self.AudioFilesList.setColumnWidth(i[0],i[1])
        
        self.RemoveSelecteAudioButton = QPushButton(self.Import)
        self.RemoveSelecteAudioButton.setObjectName(u"RemoveSelecteAudioButton")
        self.RemoveSelecteAudioButton.setGeometry(QRect(510, 137, 130, 24))
        self.RemoveSelecteAudioButton.clicked.connect(self.RemoveAudiofile)

        self.ImportRecordingGroupBox = QGroupBox(self.Import)
        self.ImportRecordingGroupBox.setObjectName(u"ImportRecordingGroupBox")
        self.ImportRecordingGroupBox.setGeometry(QRect(10, 20, 491, 141))

        self.ImportRecordingButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingButton.setObjectName(u"ImportRecordingButton")
        self.ImportRecordingButton.setGeometry(QRect(10, 110, 101, 24))
        self.ImportRecordingButton.clicked.connect(self.ValidateAudioImport)

        self.ImportRecordingName = QLineEdit(self.ImportRecordingGroupBox)
        self.ImportRecordingName.setObjectName(u"ImportRecordingName")
        self.ImportRecordingName.setGeometry(QRect(10, 80, 271, 22))
        
        self.NameInprojectLabel = QLabel(self.ImportRecordingGroupBox)
        self.NameInprojectLabel.setObjectName(u"NameInprojectLabel")
        self.NameInprojectLabel.setGeometry(QRect(10, 60, 91, 16))

        self.ImportRecordingDataPath = QLineEdit(self.ImportRecordingGroupBox)
        self.ImportRecordingDataPath.setObjectName(u"ImportRecordingDataPath")
        self.ImportRecordingDataPath.setGeometry(QRect(80, 30, 401, 22))

        self.ImportRecordingSelectFileButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingSelectFileButton.setObjectName(u"ImportRecordingSelectFileButton")
        self.ImportRecordingSelectFileButton.setGeometry(QRect(10, 30, 61, 24))
        self.ImportRecordingSelectFileButton.clicked.connect(self.ImportAudioFile)

        self.MainTabs.addTab(self.Import, "")

                                                       #    SLICE TAB

        self.Slice = QWidget()
        self.Slice.setObjectName(u"Slice")

        self.Sample_Cut_Data_Table = QTableWidget(self.Slice)
        self.Sample_Cut_Data_Table.setObjectName(u"Sample_Cut_Data_Table")
        Sample_Cut_Data_Table_length = 741
        self.Sample_Cut_Data_Table.setGeometry(QRect(230, 90, Sample_Cut_Data_Table_length, 431))
        Data_Table_Widths = ((0,30),(1,100),(2,100),(3,100))
        self.Sample_Cut_Data_Table.setColumnCount(5)
        self.Sample_Cut_Data_Table.setHorizontalHeaderLabels(("ID", "S. Start", "S. End", "Length", "Sample Groups"))
        leftover = 0
        for i in Data_Table_Widths:
            self.Sample_Cut_Data_Table.setColumnWidth(i[0],i[1])
            leftover += i[1]
        
        self.Sample_Cut_Data_Table.setColumnWidth(4,Sample_Cut_Data_Table_length-leftover-4)
        self.Add_Sample_Cut_Data = QPushButton(self.Slice)
        self.Add_Sample_Cut_Data.setObjectName(u"Add_Sample_Cut_Data")
        self.Add_Sample_Cut_Data.setGeometry(QRect(530, 60, 61, 25))  # Adjusted y-coordinate to align with other widgets
        self.Add_Sample_Cut_Data.clicked.connect(self.AddNewSlice)

        self.SampleCutpointInput = ClipboardSpinBox(self.Slice, None) #paste_callback=self.paste_clipboard_to_cutpoint)
        self.SampleCutpointInput.setObjectName(u"SampleCutpointInput")
        self.SampleCutpointInput.setGeometry(QRect(230, 60, 131, 25))
        self.SampleCutpointInput.setMinimum(0)
        self.SampleCutpointInput.setMaximum(999999999)
    
        self.Remove_Sample_Cut_Data = QPushButton(self.Slice)
        self.Remove_Sample_Cut_Data.setObjectName(u"Remove_Sample_Cut_Data")
        self.Remove_Sample_Cut_Data.setGeometry(QRect(700, 60, 100, 25))  # Adjust position as needed
        self.Remove_Sample_Cut_Data.setText("Remove Row")
        #self.Remove_Sample_Cut_Data.clicked.connect(self.remove_sample_cut_data)
  
        self.SampleEndInput = ClipboardSpinBox(self.Slice, None) #paste_callback=self.paste_clipboard_to_endinput)
        self.SampleEndInput.setObjectName(u"SampleEndInput")
        self.SampleEndInput.setGeometry(QRect(370, 60, 131, 25))
        self.SampleEndInput.setMaximum(999999999)
  
        self.IsLengthCheckbox = QCheckBox(self.Slice)
        self.IsLengthCheckbox.setObjectName(u"IsLengthCheckbox")
        self.IsLengthCheckbox.setGeometry(QRect(510, 60, 16, 22))
        #self.IsLengthCheckbox.stateChanged.connect(self.update_lenght_label)
    
        self.SampleGroupSelection = QTableWidget(self.Slice)
        self.SampleGroupSelection.setObjectName(u"SampleGroupSelection")
        self.SampleGroupSelection.setGeometry(QRect(30, 90, 191, 431))
        self.SampleGroupSelection.setColumnCount(4)
        if not DEV:
            self.SampleGroupSelection.hideColumn(1)
            self.SampleGroupSelection.hideColumn(2)
            self.SampleGroupSelection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrollbar
        self.SampleGroupSelection.setColumnWidth(0, 138)
        self.SampleGroupSelection.setColumnWidth(1, 10)
        self.SampleGroupSelection.setColumnWidth(2, 10)
        self.SampleGroupSelection.setColumnWidth(3, 10)
        self.SampleGroupSelection.verticalHeader().setVisible(False)
        self.SampleGroupSelection.horizontalHeader().setVisible(False)
        
        self.SampleGroupSelection.clicked.connect(self.UpdateSelectedSGroup)

        self.SliceGroupAllButton = QPushButton(self.Slice)
        self.SliceGroupAllButton.setObjectName(u"SliceGroupAllButton")
        self.SliceGroupAllButton.setGeometry(QRect(120, 60, 51, 24))
        self.SliceGroupAllButton.clicked.connect(self.SelectAllSampleGroups)
       
        self.SliceGroupClearButton = QPushButton(self.Slice)
        self.SliceGroupClearButton.setObjectName(u"SliceGroupClearButton")
        self.SliceGroupClearButton.setGeometry(QRect(170, 60, 51, 24))
        self.SliceGroupClearButton.clicked.connect(self.ClearAllSampleGroups)
      
        self.labelsamplegroups = QLabel(self.Slice)
        self.labelsamplegroups.setObjectName(u"labelsamplegroups")
        self.labelsamplegroups.setGeometry(QRect(30, 60, 91, 16))
      
        self.labelsamplestart = QLabel(self.Slice)
        self.labelsamplestart.setObjectName(u"label_2")
        self.labelsamplestart.setGeometry(QRect(230, 40, 131, 16))
       
        self.labelsampleend = QLabel(self.Slice)
        self.labelsampleend.setObjectName(u"label_3")
        self.labelsampleend.setGeometry(QRect(370, 40, 131, 16))
      
        self.AutoClipboardCheckbox = QCheckBox(self.Slice)
        self.AutoClipboardCheckbox.setObjectName(u"AutoClipboardCheckbox")
        self.AutoClipboardCheckbox.setGeometry(QRect(600, 60, 150, 25))
        self.AutoClipboardCheckbox.setText("Auto Clipboard")
       
        self.MainTabs.addTab(self.Slice, "")

                                                              #    SORT TAB    
 
        self.Sort = QWidget()
        self.Sort.setObjectName(u"sort")

        self.SortGroupSlices = QGroupBox(self.Sort)
        self.SortGroupSlices.setObjectName(u"SortGroupSlices")
        self.SortGroupSlices.setGeometry(QRect(10, 40, 201, 491))
     
        self.SortTabSliceList = QTableWidget(self.SortGroupSlices)
        self.SortTabSliceList.setObjectName(u"SortTabSliceList")
        self.SortTabSliceList.setGeometry(QRect(10, 20, 181, 461))
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
    
        self.SortTabSGroupfilter = QComboBox(self.Sort)
        self.SortTabSGroupfilter.addItem("")
        self.SortTabSGroupfilter.setObjectName(u"SortTabSGroupfilter")
        self.SortTabSGroupfilter.setGeometry(QRect(10, 10, 201, 24))
        self.SortTabSGroupfilter.currentIndexChanged.connect(self.SortTabSliceListUpdate)
        #self.SortTabSGroupfilter.currentIndexChanged.connect(self.update_sort_preview_audio_select)
     
        self.SortAudioPreview = QGroupBox(self.Sort)
        self.SortAudioPreview.setObjectName(u"SortAudioPreview")
        self.SortAudioPreview.setGeometry(QRect(220, 10, 551, 251))
     
        self.AudioPreviewContainer = QWidget(self.SortAudioPreview)
        self.AudioPreviewContainer.setGeometry(QRect(10, 20, 531, 161))
        self.AudioPreviewContainer.setObjectName(u"AudioPreviewContainer")

        self.WaveformVisu = pg.PlotWidget(self.AudioPreviewContainer)
        self.WaveformVisu.setGeometry(QRect(0, 0, 531, 161))
        self.WaveformVisu.setObjectName(u"AudioPreviewPlaceholder")
        self.WaveformVisu.setBackground("lightgray")  # Set background color
        self.WaveformVisu.showGrid(x=False, y=False)  # Hide grid
        self.WaveformVisu.getPlotItem().hideAxis("bottom")  # Hide x-axis
        self.WaveformVisu.getPlotItem().hideAxis("left")  # Hide y-axis
        self.WaveformVisu.getPlotItem().setMenuEnabled(False)  # Disable context menu
        self.WaveformVisu.getPlotItem().setLimits(yMin=-1, yMax=1)  # Limit y-axis to -1 to +1
        self.WaveformVisu.setMouseEnabled(x=True, y=False)      # Disable vertical drag
        self.WaveformVisu.plotItem.setMenuEnabled(False)        # Hide context menu
        self.WaveformVisu.plotItem.setMouseEnabled(y=False)     # Ensure vertical zoom/drag is off
        #self.AudioPreviewPlaceholder.sigRangeChanged.connect(self.on_waveform_range_changed)

        self.SortPreviewPlayButton = QPushButton(self.SortAudioPreview)
        self.SortPreviewPlayButton.setObjectName(u"SortPreviewPlayButton")
        self.SortPreviewPlayButton.setGeometry(QRect(10, 190, 71, 24))
        #self.SortPreviewPlayButton.clicked.connect(self.play_audio_sample)

        self.SortPreviewStopButton = QPushButton(self.SortAudioPreview)
        self.SortPreviewStopButton.setObjectName(u"SortPreviewStopButton")
        self.SortPreviewStopButton.setGeometry(QRect(10, 220, 71, 24))
        #self.SortPreviewStopButton.clicked.connect(self.stop_audio_sample)
   
        self.SortPreviewVolume = QSlider(self.SortAudioPreview)
        self.SortPreviewVolume.setObjectName(u"SortPreviewVolume")
        self.SortPreviewVolume.setGeometry(QRect(90, 210, 160, 20))
        self.SortPreviewVolume.setOrientation(Qt.Orientation.Horizontal)
        self.SortPreviewVolume.setMaximum(10000)
        self.SortPreviewVolume.setSingleStep(1)
        self.SortPreviewVolume.setMinimum(0)
        self.SortPreviewVolume.setValue(10000)
   
        self.SortPreviewAudioSelect = QComboBox(self.SortAudioPreview)
        self.SortPreviewAudioSelect.setObjectName(u"SortPreviewAudioSelect")
        self.SortPreviewAudioSelect.setGeometry(QRect(381, 190, 161, 24))
        #self.SortPreviewAudioSelect.currentIndexChanged.connect(self.update_waveform_preview)
     
        self.LabelPlaybackVolume = QLabel(self.SortAudioPreview)
        self.LabelPlaybackVolume.setObjectName(u"LabelPlaybackVolume")
        self.LabelPlaybackVolume.setGeometry(QRect(90, 190, 161, 20))
     
        self.SortSetup = QGroupBox(self.Sort)
        self.SortSetup.setObjectName(u"SortSetup")
        self.SortSetup.setGeometry(QRect(780, 10, 431, 251))
     
        self.SortSetupRRSelection = QSpinBox(self.SortSetup)
        self.SortSetupRRSelection.setObjectName(u"SortSetupRRSelection")
        self.SortSetupRRSelection.setGeometry(QRect(10, 40, 111, 21))
        self.LabelSortRRSelection = QLabel(self.SortSetup)
        self.LabelSortRRSelection.setObjectName(u"LabelSortRRSelection")
        self.LabelSortRRSelection.setGeometry(QRect(10, 20, 81, 16))

        self.SortNoteConfig = QGroupBox(self.Sort)
        self.SortNoteConfig.setObjectName(u"SortNoteConfig")
        self.SortNoteConfig.setGeometry(QRect(220, 270, 551, 120))  # Positioned under Audio Preview
        self.SortNoteConfig.setTitle("Note Configuration")

        # Octave Selection
        self.OctaveLabel = QLabel(self.SortNoteConfig)
        self.OctaveLabel.setObjectName(u"OctaveLabel")
        self.OctaveLabel.setGeometry(QRect(10, 30, 60, 20))
        self.OctaveLabel.setText("Octave:")

        self.OctaveSelect = QSpinBox(self.SortNoteConfig)
        self.OctaveSelect.setObjectName(u"OctaveSelect")
        self.OctaveSelect.setGeometry(QRect(70, 30, 60, 22))
        self.OctaveSelect.setMinimum(0)
        self.OctaveSelect.setMaximum(10)
        self.OctaveSelect.setValue(4)  # Default value

        # Note Selection
        self.NoteLabel = QLabel(self.SortNoteConfig)
        self.NoteLabel.setObjectName(u"NoteLabel")
        self.NoteLabel.setGeometry(QRect(150, 30, 60, 20))
        self.NoteLabel.setText("Note:")

        self.NoteSelect = QComboBox(self.SortNoteConfig)
        self.NoteSelect.setObjectName(u"NoteSelect")
        self.NoteSelect.setGeometry(QRect(200, 30, 100, 22))
        self.NoteSelect.addItems(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])

        # Round Robin Selection
        self.RRLabel = QLabel(self.SortNoteConfig)
        self.RRLabel.setObjectName(u"RRLabel")
        self.RRLabel.setGeometry(QRect(320, 30, 100, 20))
        self.RRLabel.setText("Round Robin:")

        self.RRSelect = QSpinBox(self.SortNoteConfig)
        self.RRSelect.setObjectName(u"RRSelect")
        self.RRSelect.setGeometry(QRect(400, 30, 60, 22))
        self.RRSelect.setMinimum(1)
        self.RRSelect.setMaximum(10)
        self.RRSelect.setValue(1)  # Default value

        # Accept Button
        self.AcceptButton = QPushButton(self.SortNoteConfig)
        self.AcceptButton.setObjectName(u"AcceptButton")
        self.AcceptButton.setGeometry(QRect(10, 70, 120, 24))
        self.AcceptButton.setText("Accept")
        #self.AcceptButton.clicked.connect(self.accept_note_config)

        # Accept+Next Button
        self.AcceptNextButton = QPushButton(self.SortNoteConfig)
        self.AcceptNextButton.setObjectName(u"AcceptNextButton")
        self.AcceptNextButton.setGeometry(QRect(140, 70, 120, 24))
        self.AcceptNextButton.setText("Accept+Next")
        #self.AcceptNextButton.clicked.connect(self.accept_note_config_and_next)

        # Frequency Label
        self.FrequencyLabel = QLabel(self.SortAudioPreview)
        self.FrequencyLabel.setObjectName(u"FrequencyLabel")
        self.FrequencyLabel.setGeometry(QRect(10, 160, 200, 20))  # Adjust position as needed
        self.FrequencyLabel.setText("Frequency: N/A")

        # Note Label
        self.NoteLabel = QLabel(self.SortAudioPreview)
        self.NoteLabel.setObjectName(u"NoteLabel")
        self.NoteLabel.setGeometry(QRect(220, 160, 200, 20))  # Adjust position as needed
        self.NoteLabel.setText("Note: N/A")

        # Detect Transient Button
        self.DetectTransientButton = QPushButton(self.SortNoteConfig)
        self.DetectTransientButton.setObjectName(u"DetectTransientButton")
        self.DetectTransientButton.setGeometry(QRect(270, 70, 120, 24))  # Adjust position as needed
        self.DetectTransientButton.setText("Detect Transient")
        #self.DetectTransientButton.clicked.connect(self.detect_and_plot_transient)

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
        self.RenameSampleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Rename Sgroup", None))
        self.RenameSampleGroupEdit.setText("")
        self.RenameSampleGroupConfig.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.SampleGroupMove.setTitle(QCoreApplication.translate("MainWindow", u"Move", None))
        self.SampleGroupMoveUp.setText(QCoreApplication.translate("MainWindow", u"Up", None))
        self.SampleGroupMoveDown.setText(QCoreApplication.translate("MainWindow", u"Down", None))
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
        self.RenameSampleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Rename Sgroup", None))
        self.RenameSampleGroupEdit.setText("")
        self.RenameSampleGroupConfig.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.SampleGroupMove.setTitle(QCoreApplication.translate("MainWindow", u"Move", None))
        self.SampleGroupMoveUp.setText(QCoreApplication.translate("MainWindow", u"Up", None))
        self.SampleGroupMoveDown.setText(QCoreApplication.translate("MainWindow", u"Down", None))
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
        self.SortSetup.setTitle(QCoreApplication.translate("MainWindow", u"Setup", None))
        self.LabelSortRRSelection.setText(QCoreApplication.translate("MainWindow", u"Round Robins", None))
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
        settings = QSettings("BaSlicer", "FileDialogs") 
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
        print("New project created.")

        # Update UI stuff
        self.UpdateEverything()

    def LoadSaveFile(self):
        """
        Load shtuff
        """

        self.NotSavedPrompt("You have unsaved changes. Do you want to save before loading a new project?")

        settings = QSettings("BaSlicer", "FileDialogs")
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
        settings = QSettings("BaSlicer", "FileDialogs")
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

    def WaveformPlot(self, audio_data):
        """
        Plot the waveform of the audio data.
        """
        if audio_data is None:
            print("No audio data to plot.")
            return

        # Create a new figure
        self.WaveformVisu.figure(figsize=(10, 4))
        self.WaveformVisu.plot(audio_data)
        self.WaveformVisu.title("Waveform")
        self.WaveformVisu.xlabel("Sample Index")
        self.WaveformVisu.ylabel("Amplitude")
        self.WaveformVisu.grid()
        self.WaveformVisu.show()

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
        
        Audio_Names , Audio_Data = self.GetAudioData(SliceObject)

        if Audio_Names is None or Audio_Data is None:
            print("Error getting audio data.")
            return
        
        # Populate audio selection scrollbox


        sgroup_audio_files = []
        for sgroup in SliceObject.sample_groups:
            for audio_file in sgroup.audio_files:
                if audio_file not in sgroup_audio_files:
                    sgroup_audio_files.append(audio_file)

        self.SortPreviewAudioSelect.clear()
        for audio_file in sgroup_audio_files:
            self.SortPreviewAudioSelect.addItem(audio_file.name)

        # Populate audio preview

        #get selected audio file
        selected_audio = self.SortPreviewAudioSelect.currentText()
        #get audio data from cache
        audio_data = None
        for tup in self.CACHEDAUDIOFILES:
            if tup[0] == SliceObject.UID and tup[1] == selected_audio:
                audio_data = tup[2]
                break

        if audio_data is None:
            print("Audio data for selected file not found in cache.")
            return

        print(f"Loaded audio data for {selected_audio}")

        # Plot the waveform
        self.WaveformPlot(audio_data)
                                                         # REDO ALL AUDIO LOADING THINGS
            

    def GetAudioData(self, slice):
        """
        Get cached audio data for the selected slice.
        """
        if type(slice) != Slice:
            print("Invalid slice object.")
            return None, None

        if self.CheckSliceAudioCache(slice):
            print("Slice audio data already cached.")
        else:
            print("Slice audio data not cached, caching now.")
            self.CacheSliceAudioData(slice)

        # Check if slice uid is in cached list
        for tuple in self.CACHEDAUDIOFILES:
            if tuple[0] == slice.UID:
                print("Slice audio data already cached.")
                return tuple[1], tuple[2]
            
        return None, None

    def CheckSliceAudioCache(self, slice):
        """
        Check if audio data for the selected slice is already cached.
        """
        if type(slice) != Slice:
            print("Invalid slice object.")
            return

        # Check if slice uid is in cached list
        for tuple in self.CACHEDAUDIOFILES:
            if tuple[0] == slice.UID:
                if tuple[1] == slice.audio_file.name:
                    print("Slice audio data already cached.")
                    return True

        print("Slice audio data not cached.")
        return False

    def CacheSliceAudioData(self, slice):
        """
        Cache audio data for the selected slice.
        """
        if type(slice) != Slice:
            print("Invalid slice object.")
            return
        
        # Check if audio data is already cached
        if self.CheckSliceAudioCache(slice):
            print("Slice audio data already cached.")
            return

        #Get slice audio files
        slice_audio_files = []
        for sgroup in slice.sample_groups:
            for audio_file in sgroup.audio_files:
                if audio_file not in slice_audio_files:
                    slice_audio_files.append(audio_file)

        #Cache audio files
        for audio_file in slice_audio_files:
            self.CacheAudioFile(audio_file, slice.UID)  

    def CacheAudioFile(self, audio_file, UID):
        """
        Cache audio data for the selected audio file.
        """
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
                audio_data = wav_file.read()
                audio_data = np.frombuffer(audio_data, dtype=np.int16)
                print(audio_data)

        except Exception as e:
            print(f"Error loading audio file: {e}")
            return

        # Cache the audio data
        self.CACHEDAUDIOFILES.append((UID, audio_file.name, audio_data))
        print(f"Audio file {audio_file.name} cached successfully.")

    def SliceUIDToObject(self, uid):
        """
        Return the slice object corresponding to the given UID.
        """
        for slice in self.SLICES:
            if slice.UID == uid:
                return slice
        return None

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

def ConverTo16bInt(raw_data, bits_per_sample, sample_format='PCM'):
    """
    Convert raw audio bytes of any supported bit depth/format to 16-bit PCM.

    Args:
        raw_data (bytes): The raw audio byte stream.
        bits_per_sample (int): Bit depth of the input data (8, 16, 24, 32, 64).
        sample_format (str): 'PCM' or 'FLOAT'.

    Returns:
        np.ndarray: 16-bit integer numpy array.
    """
    if sample_format.upper() == 'FLOAT':
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

    elif sample_format.upper() == 'PCM':
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
