from ast import Import
import pickle
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
    def __init__(self, start, end, length, sample_groups, samples=None):

        self.start = start
        self.end = end
        self.length = length
        self.sample_groups = sample_groups
        self.samples = samples if samples is not None else []

class Slice:
    def __init__(self, start, end, sample_groups, ):
        self.start = start
        self.end = end
        self.sample_groups = sample_groups 

    def __repr__(self):
        return f"AudioSample({self.start}, {self.end}, {self.sample_groups})"

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

        self.SliceTabSelectedSGroups = []

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
        self.SampleGroupSelection.setColumnWidth(0, 138)
        self.SampleGroupSelection.setColumnWidth(1, 10)
        self.SampleGroupSelection.setColumnWidth(2, 10)
        self.SampleGroupSelection.setColumnWidth(3, 10)
        self.SampleGroupSelection.verticalHeader().setVisible(False)
        self.SampleGroupSelection.horizontalHeader().setVisible(False)
        self.SampleGroupSelection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrollbar
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
        self.AutoClipboardCheckbox.setGeometry(QRect(600, 60, 150, 25))  # Adjust position as needed
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
    
        self.SortTabSGroupfilter = QComboBox(self.Sort)
        self.SortTabSGroupfilter.addItem("")
        self.SortTabSGroupfilter.setObjectName(u"SortTabSGroupfilter")
        self.SortTabSGroupfilter.setGeometry(QRect(10, 10, 201, 24))
        #self.SortTabSGroupfilter.currentIndexChanged.connect(self.update_sort_tab_slice_list)
        #self.SortTabSGroupfilter.currentIndexChanged.connect(self.update_sort_preview_audio_select)
     
        self.SortAudioPreview = QGroupBox(self.Sort)
        self.SortAudioPreview.setObjectName(u"SortAudioPreview")
        self.SortAudioPreview.setGeometry(QRect(220, 10, 551, 251))
     
        self.AudioPreviewContainer = QWidget(self.SortAudioPreview)
        self.AudioPreviewContainer.setGeometry(QRect(10, 20, 531, 161))
        self.AudioPreviewContainer.setObjectName(u"AudioPreviewContainer")

        self.AudioPreviewPlaceholder = pg.PlotWidget(self.AudioPreviewContainer)
        self.AudioPreviewPlaceholder.setGeometry(QRect(0, 0, 531, 161))
        self.AudioPreviewPlaceholder.setObjectName(u"AudioPreviewPlaceholder")
        self.AudioPreviewPlaceholder.setBackground("lightgray")  # Set background color
        self.AudioPreviewPlaceholder.showGrid(x=False, y=False)  # Hide grid
        self.AudioPreviewPlaceholder.getPlotItem().hideAxis("bottom")  # Hide x-axis
        self.AudioPreviewPlaceholder.getPlotItem().hideAxis("left")  # Hide y-axis
        self.AudioPreviewPlaceholder.getPlotItem().setMenuEnabled(False)  # Disable context menu
        self.AudioPreviewPlaceholder.getPlotItem().setLimits(yMin=-1, yMax=1)  # Limit y-axis to -1 to +1
        self.AudioPreviewPlaceholder.setMouseEnabled(x=True, y=False)      # Disable vertical drag
        self.AudioPreviewPlaceholder.plotItem.setMenuEnabled(False)        # Hide context menu
        self.AudioPreviewPlaceholder.plotItem.setMouseEnabled(y=False)     # Ensure vertical zoom/drag is off
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


        # Update the UI with loaded data
        self.UpdateEverything()

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
        self.UpdateSliceTab()
        self.UpdateImportTab()

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
        new_slice = Slice(startpoint, endpoint, selected_groups)

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

    def UpdateEverything(self):
        """
        Update all UI elements in the main window.
        """
        self.UpdateImportTab()
        self.UpdateSliceTab()

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
