import json
import os
import struct
from tracemalloc import start
import wave
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
from PySide6.QtGui import QCloseEvent, QAction
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
    def __init__(self, start, end, sample_groups):
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
        self.audio_files = []
        self.sample_groups = []
        self.slices = []
        self.audio_samples = []

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
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        #self.actionOpen.triggered.connect(self.load_project)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        #self.actionSave.triggered.connect(self.save_project)
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
        self.ImporttabSampleGroupList.setColumnCount(3)
        self.ImporttabSampleGroupList.setColumnWidth(0, 190)
        if not DEV:
            self.ImporttabSampleGroupList.hideColumn(1)
            self.ImporttabSampleGroupList.hideColumn(2)
        self.ImporttabSampleGroupList.verticalHeader().setVisible(False)
        self.ImporttabSampleGroupList.horizontalHeader().setVisible(False)
        self.ImporttabSampleGroupList.setSelectionBehavior(QTableWidget.SelectRows)
        self.ImporttabSampleGroupList.setSelectionMode(QTableWidget.SingleSelection)
        #self.ImporttabSampleGroupList.clicked.connect(self.updateSamplegrouplist)

        self.AddSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        self.AddSampleGroupBox.setObjectName(u"AddSampleGroupBox")
        self.AddSampleGroupBox.setGeometry(QRect(210, 10, 221, 51))

        self.AddSampleGroupNameEdit = QLineEdit(self.AddSampleGroupBox)
        self.AddSampleGroupNameEdit.setObjectName(u"AddSampleGroupNameEdit")
        self.AddSampleGroupNameEdit.setGeometry(QRect(10, 20, 171, 22))

        self.AddSampleGroupconfirm = QPushButton(self.AddSampleGroupBox)
        self.AddSampleGroupconfirm.setObjectName(u"AddSampleGroupconfirm")
        self.AddSampleGroupconfirm.setGeometry(QRect(190, 20, 21, 24))
        #self.AddSampleGroupconfirm.clicked.connect(self.add_sample_group)

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
        #self.SampleGroupRemove.clicked.connect(self.delete_selected_sample_groups)

        self.SampleGroupClone = QPushButton(self.SampleGroupEdit)
        self.SampleGroupClone.setObjectName(u"SampleGroupClone")
        self.SampleGroupClone.setGeometry(QRect(10, 50, 51, 24))
        #self.SampleGroupClone.clicked.connect(self.clonesamplegroup)

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

        self.AddAudioToSGroup = QPushButton(self.SampleGroupConfig)
        self.AddAudioToSGroup.setObjectName(u"AddAudioToSGroup")
        self.AddAudioToSGroup.setGeometry(QRect(210, 210, 221, 24))
        #self.AddAudioToSGroup.clicked.connect(self.add_selected_audio_to_sgroup)

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
        self.RemoveSelecteAudioButton.setGeometry(QRect(320, 134, 180, 24))
        #self.RemoveSelecteAudioButton.clicked.connect(self.remove_selected_audio_file)

        self.ImportRecordingGroupBox = QGroupBox(self.Import)
        self.ImportRecordingGroupBox.setObjectName(u"ImportRecordingGroupBox")
        self.ImportRecordingGroupBox.setGeometry(QRect(10, 20, 291, 141))

        self.ImportRecordingButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingButton.setObjectName(u"ImportRecordingButton")
        self.ImportRecordingButton.setGeometry(QRect(10, 110, 101, 21))
        #self.ImportRecordingButton.clicked.connect(self.add_audio_file_to_project)

        self.ImportRecordingName = QLineEdit(self.ImportRecordingGroupBox)
        self.ImportRecordingName.setObjectName(u"ImportRecordingName")
        self.ImportRecordingName.setGeometry(QRect(10, 80, 271, 22))
        
        self.NameInprojectLabel = QLabel(self.ImportRecordingGroupBox)
        self.NameInprojectLabel.setObjectName(u"NameInprojectLabel")
        self.NameInprojectLabel.setGeometry(QRect(10, 60, 91, 16))

        self.ImportRecordingDataPath = QLineEdit(self.ImportRecordingGroupBox)
        self.ImportRecordingDataPath.setObjectName(u"ImportRecordingDataPath")
        self.ImportRecordingDataPath.setGeometry(QRect(80, 30, 201, 22))

        self.ImportRecordingSelectFileButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingSelectFileButton.setObjectName(u"ImportRecordingSelectFileButton")
        self.ImportRecordingSelectFileButton.setGeometry(QRect(10, 30, 61, 24))
        #self.ImportRecordingSelectFileButton.clicked.connect(self.import_audio_file)

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
        #self.Add_Sample_Cut_Data.clicked.connect(self.add_sample_cut_point)

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
        self.SampleGroupSelection.setColumnWidth(0, 158)
        self.SampleGroupSelection.setColumnWidth(3, 10)
        self.SampleGroupSelection.verticalHeader().setVisible(False)
        self.SampleGroupSelection.horizontalHeader().setVisible(False)
        self.SampleGroupSelection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrollbar

        self.SliceGroupAllButton = QPushButton(self.Slice)
        self.SliceGroupAllButton.setObjectName(u"SliceGroupAllButton")
        self.SliceGroupAllButton.setGeometry(QRect(120, 60, 51, 24))
        #self.SliceGroupAllButton.clicked.connect(self.select_all_sample_groups)
       
        self.SliceGroupClearButton = QPushButton(self.Slice)
        self.SliceGroupClearButton.setObjectName(u"SliceGroupClearButton")
        self.SliceGroupClearButton.setGeometry(QRect(170, 60, 51, 24))
        #self.SliceGroupClearButton.clicked.connect(self.clear_all_sample_groups)
      
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
        self.AddAudioToSGroup.setText(QCoreApplication.translate("MainWindow", u"Add audio to current group", None))
        self.RemoveAudioGromSGroup.setText(QCoreApplication.translate("MainWindow", u"Remove from current group", None))
        self.AudioFilesListGroup.setTitle(QCoreApplication.translate("MainWindow", u"Audio Files", None))
        self.ImportRecordingGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Import Recording", None))
        self.ImportRecordingButton.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.ImportRecordingName.setText("")
        self.NameInprojectLabel.setText(QCoreApplication.translate("MainWindow", u"Name in project", None))
        self.ImportRecordingDataPath.setText(QCoreApplication.translate("MainWindow", u"    . . .", None))
        self.ImportRecordingSelectFileButton.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.RemoveSelecteAudioButton.setText(QCoreApplication.translate("MainWindow", u"Remove Selected Audio File", None))
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
        self.AddAudioToSGroup.setText(QCoreApplication.translate("MainWindow", u"Add audio to current group", None))
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
