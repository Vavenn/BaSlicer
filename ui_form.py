from asyncio.windows_events import NULL
import json
from logging import NullHandler
import os
from email.errors import MessageParseError
from re import S
from PySide6.QtCore import *    #YOLO
from PySide6 import QtCore
from PySide6.QtGui import *    #YOLO
from PySide6.QtWidgets import *    #YOLO
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from pathlib import Path
import wave
import numpy as np
import contextlib
import ast as scholar
import pyqtgraph as pg
import wave
import struct
import sounddevice as sd
from scipy.signal import correlate
import shutil

_current_stream = None

NOTE_NAMES = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
]

class ClipboardSpinBox(QSpinBox):
    def __init__(self, parent=None, paste_callback=None):
        super().__init__(parent)
        self.paste_callback = paste_callback

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.paste_callback:
            self.paste_callback()
            
class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1227, 604)
        self.project_file_path = ""
        
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionOpen.triggered.connect(self.load_project)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave.triggered.connect(self.save_project)
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")


        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.MainTabs = QTabWidget(self.centralwidget)
        self.MainTabs.currentChanged.connect(self.updatetabs)

        self.MainTabs.setObjectName(u"MainTabs")
        self.MainTabs.setGeometry(QRect(-4, -1, 1251, 571))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.MainTabs.sizePolicy().hasHeightForWidth())
        self.MainTabs.setSizePolicy(sizePolicy)
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
        self.ImporttabSampleGroupList.hideColumn(1)
        self.ImporttabSampleGroupList.hideColumn(2)
        self.ImporttabSampleGroupList.verticalHeader().setVisible(False)
        self.ImporttabSampleGroupList.horizontalHeader().setVisible(False)
        self.ImporttabSampleGroupList.setSelectionBehavior(QTableWidget.SelectRows)
        self.ImporttabSampleGroupList.setSelectionMode(QTableWidget.SingleSelection)
        self.ImporttabSampleGroupList.clicked.connect(self.updateSamplegrouplist)

        self.AddSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        self.AddSampleGroupBox.setObjectName(u"AddSampleGroupBox")
        self.AddSampleGroupBox.setGeometry(QRect(210, 10, 221, 51))
        self.AddSampleGroupNameEdit = QLineEdit(self.AddSampleGroupBox)
        self.AddSampleGroupNameEdit.setObjectName(u"AddSampleGroupNameEdit")
        self.AddSampleGroupNameEdit.setGeometry(QRect(10, 20, 171, 22))
        self.AddSampleGroupconfirm = QPushButton(self.AddSampleGroupBox)
        self.AddSampleGroupconfirm.setObjectName(u"AddSampleGroupconfirm")
        self.AddSampleGroupconfirm.setGeometry(QRect(190, 20, 21, 24))
        self.AddSampleGroupconfirm.clicked.connect(self.AddSampleGroup)
        self.RenameSampleGroupBox = QGroupBox(self.SampleGroupConfig)
        self.RenameSampleGroupBox.setObjectName(u"RenameSampleGroupBox")
        self.RenameSampleGroupBox.setGeometry(QRect(210, 60, 221, 51))
        self.RenameSampleGroupEdit = QLineEdit(self.RenameSampleGroupBox)
        self.RenameSampleGroupEdit.setObjectName(u"RenameSampleGroupEdit")
        self.RenameSampleGroupEdit.setGeometry(QRect(10, 20, 171, 22))
        self.RenameSampleGroupConfig = QPushButton(self.RenameSampleGroupBox)
        self.RenameSampleGroupConfig.setObjectName(u"RenameSampleGroupConfig")
        self.RenameSampleGroupConfig.setGeometry(QRect(190, 20, 21, 24))
        self.RenameSampleGroupConfig.clicked.connect(self.RenameSampleGroup)
        self.SampleGroupMove = QGroupBox(self.SampleGroupConfig)
        self.SampleGroupMove.setObjectName(u"SampleGroupMove")
        self.SampleGroupMove.setGeometry(QRect(240, 110, 71, 91))
        self.SampleGroupMoveUp = QPushButton(self.SampleGroupMove)
        self.SampleGroupMoveUp.setObjectName(u"SampleGroupMoveUp")
        self.SampleGroupMoveUp.setGeometry(QRect(10, 20, 51, 24))
        self.SampleGroupMoveUp.clicked.connect(self.sgroupmoveup)
        self.SampleGroupMoveDown = QPushButton(self.SampleGroupMove)
        self.SampleGroupMoveDown.setObjectName(u"SampleGroupMoveDown")
        self.SampleGroupMoveDown.setGeometry(QRect(10, 50, 51, 24))
        self.SampleGroupMoveDown.clicked.connect(self.sgroupmovedown)
        self.SampleGroupEdit = QGroupBox(self.SampleGroupConfig)
        self.SampleGroupEdit.setObjectName(u"SampleGroupEdit")
        self.SampleGroupEdit.setGeometry(QRect(330, 110, 71, 91))
        self.SampleGroupRemove = QPushButton(self.SampleGroupEdit)
        self.SampleGroupRemove.setObjectName(u"SampleGroupRemove")
        self.SampleGroupRemove.setGeometry(QRect(10, 20, 51, 24))
        self.SampleGroupRemove.clicked.connect(self.deletesamplegroup)
        self.SampleGroupClone = QPushButton(self.SampleGroupEdit)
        self.SampleGroupClone.setObjectName(u"SampleGroupClone")
        self.SampleGroupClone.setGeometry(QRect(10, 50, 51, 24))
        self.SampleGroupClone.clicked.connect(self.clonesamplegroup)
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
        self.AddAudioToSGroup.clicked.connect(self.add_selected_audio_to_sgroup)
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
        self.AudioFilesList.hideColumn(6)
        self.AudioFilesList.setSelectionBehavior(QTableWidget.SelectRows)
        self.AudioFilesList.setHorizontalHeaderLabels(("Name", "File", "Channels", "Sample Rate", "Bit Depth", "Lenght", "id"))
        AudioFilesTableWidths = ((0,80),(1,284),(2,55),(3,75),(4,55),(5,60),(6,30))
        for i in AudioFilesTableWidths:
            self.AudioFilesList.setColumnWidth(i[0],i[1])
        

        self.ImportRecordingGroupBox = QGroupBox(self.Import)
        self.ImportRecordingGroupBox.setObjectName(u"ImportRecordingGroupBox")
        self.ImportRecordingGroupBox.setGeometry(QRect(10, 20, 291, 141))
        self.ImportRecordingButton = QPushButton(self.ImportRecordingGroupBox)
        self.ImportRecordingButton.setObjectName(u"ImportRecordingButton")
        self.ImportRecordingButton.setGeometry(QRect(10, 110, 101, 21))

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
        self.MainTabs.addTab(self.Import, "")
        MainWindow.setCentralWidget(self.centralwidget)



        self.MainTabs.setCurrentIndex(0)


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




    #                                                -=-=-=-=-=-=-----=-=--=-=-=--=-==--= SLICE TAB


        self.Slice = QWidget()
        self.Slice.setObjectName(u"Slice")
        self.Sample_Cut_Data_Table = QTableWidget(self.Slice)
        self.Sample_Cut_Data_Table.setObjectName(u"Sample_Cut_Data_Table")
        Sample_Cut_Data_Table_length = 741
        self.Sample_Cut_Data_Table.setGeometry(QRect(230, 90, Sample_Cut_Data_Table_length, 431))
        self.Add_Sample_Cut_Data = QPushButton(self.Slice)
        self.Add_Sample_Cut_Data.setObjectName(u"Add_Sample_Cut_Data")
        self.Add_Sample_Cut_Data.setGeometry(QRect(530, 60, 61, 25))  # Adjusted y-coordinate to align with other widgets
        self.SampleCutpointInput = ClipboardSpinBox(self.Slice, paste_callback=self.paste_clipboard_to_cutpoint)
        self.SampleCutpointInput.setObjectName(u"SampleCutpointInput")
        self.SampleCutpointInput.setGeometry(QRect(230, 60, 131, 25))
        self.SampleCutpointInput.setMinimum(0)
        self.SampleCutpointInput.setMaximum(999999999)
        self.Remove_Sample_Cut_Data = QPushButton(self.Slice)
        self.Remove_Sample_Cut_Data.setObjectName(u"Remove_Sample_Cut_Data")
        self.Remove_Sample_Cut_Data.setGeometry(QRect(700, 60, 100, 25))  # Adjust position as needed
        self.Remove_Sample_Cut_Data.setText("Remove Row")
        self.Remove_Sample_Cut_Data.clicked.connect(self.remove_sample_cut_data)
        self.SampleEndInput = ClipboardSpinBox(self.Slice, paste_callback=self.paste_clipboard_to_endinput)
        self.SampleEndInput.setObjectName(u"SampleEndInput")
        self.SampleEndInput.setGeometry(QRect(370, 60, 131, 25))
        self.SampleEndInput.setMaximum(999999999)
        self.IsLengthCheckbox = QCheckBox(self.Slice)
        self.IsLengthCheckbox.setObjectName(u"IsLengthCheckbox")
        self.IsLengthCheckbox.setGeometry(QRect(510, 60, 16, 22))
        self.IsLengthCheckbox.stateChanged.connect(self.update_lenght_label)
        self.SampleGroupSelection = QTableWidget(self.Slice)
        self.SampleGroupSelection.setObjectName(u"SampleGroupSelection")
        self.SampleGroupSelection.setGeometry(QRect(30, 90, 191, 431))
        self.SampleGroupSelection.setColumnCount(4)
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
        self.SliceGroupAllButton.clicked.connect(self.select_all_sample_groups)
        self.SliceGroupClearButton = QPushButton(self.Slice)
        self.SliceGroupClearButton.setObjectName(u"SliceGroupClearButton")
        self.SliceGroupClearButton.setGeometry(QRect(170, 60, 51, 24))
        self.SliceGroupClearButton.clicked.connect(self.clear_all_sample_groups)
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




                                                            # *_*_*_*_*_*_*__**_

                                                          #  -=-=-=-=--=-==--= -=--=-=--=-= SORT TAB    
        self.Sort = QWidget()
        self.Sort.setObjectName(u"sort")
        # self.WaveformWidget = PlotWidget(self.Sort)
        # self.WaveformWidget.setObjectName("WaveformWidget")
        # self.WaveformWidget.setGeometry(QRect(230, 530, 741, 150))  
        # self.WaveformWidget.setLabel('bottom', 'Time', units='s')
        # self.WaveformWidget.setLabel('left', 'Amplitude')
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
        self.SortTabSliceList.hideColumn(0)
        self.SortTabSliceList.hideColumn(3)
        self.SortTabSliceList.itemSelectionChanged.connect(self.update_waveform_preview)
        self.SortTabSGroupfilter = QComboBox(self.Sort)
        self.SortTabSGroupfilter.addItem("")
        self.SortTabSGroupfilter.setObjectName(u"SortTabSGroupfilter")
        self.SortTabSGroupfilter.setGeometry(QRect(10, 10, 201, 24))
        self.SortTabSGroupfilter.currentIndexChanged.connect(self.update_sort_tab_slice_list)
        self.SortTabSGroupfilter.currentIndexChanged.connect(self.update_sort_preview_audio_select)
        self.SortAudioPreview = QGroupBox(self.Sort)
        self.SortAudioPreview.setObjectName(u"SortAudioPreview")
        self.SortAudioPreview.setGeometry(QRect(220, 10, 551, 251))
        self.AudioPreviewContainer = QWidget(self.SortAudioPreview)
        self.AudioPreviewContainer.setGeometry(QRect(10, 20, 531, 161))
        self.AudioPreviewContainer.setObjectName(u"AudioPreviewContainer")

        self.AudioPreviewPplaceholder = pg.PlotWidget(self.AudioPreviewContainer)
        self.AudioPreviewPplaceholder.setGeometry(QRect(0, 0, 531, 161))
        self.AudioPreviewPplaceholder.setObjectName(u"AudioPreviewPplaceholder")
        self.AudioPreviewPplaceholder.setBackground("lightgray")  # Set background color
        self.AudioPreviewPplaceholder.showGrid(x=False, y=False)  # Hide grid
        self.AudioPreviewPplaceholder.getPlotItem().hideAxis("bottom")  # Hide x-axis
        self.AudioPreviewPplaceholder.getPlotItem().hideAxis("left")  # Hide y-axis
        self.AudioPreviewPplaceholder.getPlotItem().setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.AudioPreviewPplaceholder.getPlotItem().setMenuEnabled(False)  # Disable context menu
        self.AudioPreviewPplaceholder.getPlotItem().setLimits(yMin=-1, yMax=1)  # Limit y-axis to -1 to +1

        self.SortPreviewPlayButton = QPushButton(self.SortAudioPreview)
        self.SortPreviewPlayButton.setObjectName(u"SortPreviewPlayButton")
        self.SortPreviewPlayButton.setGeometry(QRect(10, 190, 71, 24))
        self.SortPreviewStopButton = QPushButton(self.SortAudioPreview)
        self.SortPreviewStopButton.setObjectName(u"SortPreviewStopButton")
        self.SortPreviewStopButton.setGeometry(QRect(10, 220, 71, 24))
        self.SortPreviewPlayButton.clicked.connect(self.play_audio_sample)
        self.SortPreviewStopButton.clicked.connect(self.stop_audio_sample)
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
        self.SortPreviewAudioSelect.currentIndexChanged.connect(self.update_waveform_preview)
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
        self.AcceptButton.clicked.connect(self.accept_note_config)

        # Accept+Next Button
        self.AcceptNextButton = QPushButton(self.SortNoteConfig)
        self.AcceptNextButton.setObjectName(u"AcceptNextButton")
        self.AcceptNextButton.setGeometry(QRect(140, 70, 120, 24))
        self.AcceptNextButton.setText("Accept+Next")
        self.AcceptNextButton.clicked.connect(self.accept_note_config_and_next)

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



                                                            # *_*_*_*_*_*_*_*__**_
                                                            #   EXPORT TAB -=-=-=-=--==--=
        self.Export = QWidget()
        self.Export.setObjectName(u"Export")
        self.ExportFinalTable = QTableWidget(self.Export)
        self.ExportFinalTable.setObjectName(u"ExportFinalTable")
        self.ExportFinalTable.setGeometry(QRect(10, 10, 800, 400))  # Adjust size and position as needed
        self.ExportFinalTable.setColumnCount(8)
        self.ExportFinalTable.setHorizontalHeaderLabels([
            "ID", "Slice ID", "Sample Start", "Sample End", "Audio File Path", 
            "Sample Group Name", "MIDI Note", "Round Robin"
        ])
        self.ExportFinalTable.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Make the table read-only
        self.ExportFinalTable.setSelectionMode(QAbstractItemView.NoSelection)  # Disable selection

         # Export Button
        self.ExportButton = QPushButton(self.Export)
        self.ExportButton.setObjectName(u"ExportButton")
        self.ExportButton.setGeometry(QRect(820, 10, 100, 30))  # Adjust position as needed
        self.ExportButton.setText("Export")
        self.ExportButton.clicked.connect(self.export_samples)
                                                            #*_*_*_*_*_*_*_*
        self.SampleGroupSelection.setColumnCount(4)

        self.MainTabs.addTab(self.Sort, "")
        self.MainTabs.addTab(self.Export, "")
        
        self.RemoveSelecteAudioButtonA = QPushButton(self.Import)
        self.RemoveSelecteAudioButtonA.setObjectName(u"RemoveSelecteAudioButtonA")
        self.RemoveSelecteAudioButtonA.setGeometry(QRect(320, 134, 180, 24))
        self.RemoveSelecteAudioButtonA.clicked.connect(self.remove_selected_audio_file)
        self.MainTabs.setCurrentIndex(0)
        self.SampleGroups = []
        self.Data_Table_Checkboxes = []

        Data_Table_Widths = ((0,30),(1,100),(2,100),(3,100))
        self.Sample_Cut_Data_Table.setColumnCount(5)
        self.Sample_Cut_Data_Table.setHorizontalHeaderLabels(("ID", "S. Start", "S. End", "Length", "Sample Groups"))
        leftover = 0
        for i in Data_Table_Widths:
            self.Sample_Cut_Data_Table.setColumnWidth(i[0],i[1])
            leftover += i[1]
        
        self.Sample_Cut_Data_Table.setColumnWidth(4,Sample_Cut_Data_Table_length-leftover-4)


        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        self.MainTabs.setTabText(self.MainTabs.indexOf(self.Import), QCoreApplication.translate("MainWindow", u"Import", None))
        self.Add_Sample_Cut_Data.setText(QCoreApplication.translate("MainWindow", u"+", None))
        self.Add_Sample_Cut_Data.clicked.connect(self.add_sample_cut_point)
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
        self.RemoveSelecteAudioButtonA.setText(QCoreApplication.translate("MainWindow", u"Remove Selected Audio File", None))
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
        self.ImportRecordingSelectFileButton.clicked.connect(self.import_audio_file)
        self.ImportRecordingButton.clicked.connect(self.add_audio_file_to_project)
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

    def reset(self):
        self.SampleCutpointInput.clear()
        self.SampleCutpointInput.setValue(0)
        if not self.IsLengthCheckbox.isChecked():
            self.SampleEndInput.clear()
            self.SampleEndInput.setValue(0)

    def add_sample_cut_point(self):
        # Determine the new ID
        row_count = self.Sample_Cut_Data_Table.rowCount()
        if row_count > 0:
            ids = []
            for row in range(row_count):
                item = self.Sample_Cut_Data_Table.item(row, 0)  # Column 0 is the ID column
                if item:
                    ids.append(int(item.text()))
            new_id = max(ids) + 1
        else:
            new_id = 1

        # Add a new row
        row = self.Sample_Cut_Data_Table.rowCount()
        self.Sample_Cut_Data_Table.insertRow(row)

        # Set the ID
        self.Sample_Cut_Data_Table.setItem(row, 0, QTableWidgetItem(str(new_id)))

        # Set the start point
        if self.SampleCutpointInput.text() == '':
            startpoint = 0
        else:
            startpoint = int(self.SampleCutpointInput.text())
        self.Sample_Cut_Data_Table.setItem(row, 1, QTableWidgetItem(str(startpoint)))

        # Set the end point
        if self.IsLengthCheckbox.isChecked():
            endpoint = int(self.SampleEndInput.value()) + startpoint
        else:
            endpoint = int(self.SampleEndInput.value())
        self.Sample_Cut_Data_Table.setItem(row, 2, QTableWidgetItem(str(endpoint)))

        # Set the length
        self.Sample_Cut_Data_Table.setItem(row, 3, QTableWidgetItem(str(endpoint - startpoint)))

        # Collect checked sample groups
        checked_groups = []
        for i in range(self.SampleGroupSelection.rowCount()):
            checkbox_item = self.SampleGroupSelection.item(i, 3)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                group_id_item = self.SampleGroupSelection.item(i, 1)  # Assuming column 1 contains the group ID
                if group_id_item:
                    checked_groups.append(group_id_item.text())

        # Save checked groups into the "Sample Groups" column
        self.Sample_Cut_Data_Table.setItem(row, 4, QTableWidgetItem(list_to_string(checked_groups)))

        # Set row height
        self.Sample_Cut_Data_Table.setRowHeight(row, 8)

        # Reset inputs
        self.reset()

    def update_lenght_label(self):
        if self.IsLengthCheckbox.isChecked():
            self.labelsampleend.setText(QCoreApplication.translate("MainWindow", u"Length", None))
        else:
            self.labelsampleend.setText(QCoreApplication.translate("MainWindow", u"Sample End", None))

    def remove_cut_point(self):
        current_row = self.Sample_Cut_Data_Table.currentRow()
        if current_row < 0:
            return QMessageBox.warning(self, 'Warning','Please select a row to delete')

        self.Sample_Cut_Data_Table.removeRow(current_row)

    def save_project(self):
        """
        Save the current project to a file.
        """
        settings = QSettings("BaSlicer", "FileDialogs") 
        last_dir = settings.value("lastProjectSaveDir", "")

        # Check if the project file path is empty
        if self.project_file_path == "":
            save_file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Select a BaSlicer Project file",
                last_dir,
                "BasProject File (*.basproj);;All files (*)"
            )

            # If the user cancels the dialog, return early
            if not save_file_path:
                print("Save operation canceled.")
                return

            # Save the directory for future use
            settings.setValue("lastProjectSaveDir", save_file_path)

            # Ensure the file has the correct extension
            output_file = os.path.splitext(save_file_path)[0] + ".basproj"
        else:
            # Use the existing project file path
            output_file = self.project_file_path

        # Compile and save the project
        self.project_compile(output_file)
        self.project_file_path = output_file
        print(f"Project saved to {output_file}")
        return()
    
    def project_compile(self, project_path):

        Sample_Cut_Data_Table = []
        for row in range(self.Sample_Cut_Data_Table.rowCount()):
            row_data = []
            for col in range(self.Sample_Cut_Data_Table.columnCount()):
                item = self.Sample_Cut_Data_Table.item(row, col)
                row_data.append(item.text() if item else "")
            Sample_Cut_Data_Table.append(row_data)

        AudioFilesList = []
        for row in range(self.AudioFilesList.rowCount()):
            row_data = []
            for col in range(self.AudioFilesList.columnCount()):
                item = self.AudioFilesList.item(row, col)
                row_data.append(item.text() if item else "")
            AudioFilesList.append(row_data)

        ImporttabSampleGroupList = []
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            row_data = []
            for col in range(self.ImporttabSampleGroupList.columnCount()):
                item = self.ImporttabSampleGroupList.item(row, col)
                row_data.append(item.text() if item else "")
            ImporttabSampleGroupList.append(row_data)


        ExportFinalTable = []
        for row in range(self.ExportFinalTable.rowCount()):
            row_data = []
            for col in range(self.ExportFinalTable.columnCount()):
                item = self.ExportFinalTable.item(row, col)
                row_data.append(item.text() if item else "")
            ExportFinalTable.append(row_data)

        state = {
            "Sample_Cut_Data_Table": Sample_Cut_Data_Table,
            "AudioFilesList": AudioFilesList,
            "ExportFinalTable": ExportFinalTable,
            "ImporttabSampleGroupList": ImporttabSampleGroupList,
            "SampleCutpointInput":str(self.SampleCutpointInput.value()),
            "SampleEndInput":str(self.SampleEndInput.value()),
            "IsLengthCheckbox":str(self.IsLengthCheckbox.isChecked())

        }
        with open(project_path, "w") as f:
            json.dump(state, f, indent=4)
        return
    
    def load_project(self):
        settings = QSettings("BaSlicer", "FileDialogs") 

        last_dir = settings.value("lastProjectOpenDir", "")


        open_file = QFileDialog.getOpenFileName(
            None,
            "Select a BaSlicer Project file",
            last_dir,
            "BasProject File (*.basproj);;All files (*)"
        )
        if open_file:
            settings.setValue("lastProjectOpenDir", open_file[0])
            self.project_file_path = open_file[0]
            with open(open_file[0], "r") as f:
                data = json.load(f)
            
            self.SampleCutpointInput.setValue(int(data.get("SampleCutpointInput", "")))
            self.SampleEndInput.setValue(int(data.get("SampleEndInput", "")))
            self.IsLengthCheckbox.setChecked(bool(data.get("IsLengthCheckbox", False)))

            Sample_Cut_Data_Table = data.get("Sample_Cut_Data_Table", [])
            self.reset_table(self.Sample_Cut_Data_Table)
            self.Sample_Cut_Data_Table.setRowCount(len(Sample_Cut_Data_Table))

            for row_idx, row_data in enumerate(Sample_Cut_Data_Table):
                for col_idx, cell_text in enumerate(row_data):
                    item = QTableWidgetItem(cell_text)
                    self.Sample_Cut_Data_Table.setItem(row_idx, col_idx, item)
                    self.Sample_Cut_Data_Table.setRowHeight(row_idx,8)

            AudioFilesList = data.get("AudioFilesList", [])
            self.reset_table(self.AudioFilesList)
            self.AudioFilesList.setRowCount(len(AudioFilesList))

            for row_idx, row_data in enumerate(AudioFilesList):
                for col_idx, cell_text in enumerate(row_data):
                    item = QTableWidgetItem(cell_text)
                    self.AudioFilesList.setItem(row_idx, col_idx, item)
                    self.AudioFilesList.setRowHeight(row_idx,8)

            ImporttabSampleGroupList = data.get("ImporttabSampleGroupList", [])
            self.reset_table(self.ImporttabSampleGroupList)
            self.ImporttabSampleGroupList.setRowCount(len(ImporttabSampleGroupList))

            for row_idx, row_data in enumerate(ImporttabSampleGroupList):
                for col_idx, cell_text in enumerate(row_data):
                    item = QTableWidgetItem(cell_text)
                    self.ImporttabSampleGroupList.setItem(row_idx, col_idx, item)
                    self.ImporttabSampleGroupList.setRowHeight(row_idx,8)

            ExportFinalTable = data.get("ExportFinalTable", [])
            self.reset_table(self.ExportFinalTable)
            self.ExportFinalTable.setRowCount(len(ExportFinalTable))

            for row_idx, row_data in enumerate(ExportFinalTable):
                for col_idx, cell_text in enumerate(row_data):
                    item = QTableWidgetItem(cell_text)
                    self.ExportFinalTable.setItem(row_idx, col_idx, item)
                    self.ExportFinalTable.setRowHeight(row_idx, 8)


            self.update_sort_tab_sgroup_filter()

    def AddSampleGroup(self):
        name = self.AddSampleGroupNameEdit.text()
        if len(name) > 0:
            rowc = self.ImporttabSampleGroupList.rowCount()
            newid = 1  # Default ID for the first sample group
            if rowc > 0:
                ids = []
                for row in range(rowc):
                    item = self.ImporttabSampleGroupList.item(row, 1)
                    if item:
                        ids.append(int(item.text()))
                if ids:  
                    newid = max(ids) + 1

            row = self.ImporttabSampleGroupList.rowCount()

            self.ImporttabSampleGroupList.setRowCount(row + 1)
            self.ImporttabSampleGroupList.setItem(row, 0, QTableWidgetItem(name))
            self.ImporttabSampleGroupList.setItem(row, 1, QTableWidgetItem(str(newid)))
            self.AddSampleGroupNameEdit.setText("")
            self.update_sort_tab_sgroup_filter()

    def RenameSampleGroup(self):
        name = self.RenameSampleGroupEdit.text()
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if len(name)>0 and selected:
                row = selected[0].row()
                self.ImporttabSampleGroupList.setItem(row,0,QTableWidgetItem(name))
                self.RenameSampleGroupEdit.setText("")
                self.update_sort_tab_sgroup_filter()

    def import_audio_file(self):
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

    def add_audio_file_to_project(self):
        rawpath = self.ImportRecordingDataPath.text()
        path = Path(rawpath)
        name = self.ImportRecordingName.text()
        if path.is_file() and path.suffix.lower() == ".wav" and not name == "":
            rowc = self.AudioFilesList.rowCount()
            if rowc > 0:
                ids = []
                for row in range(rowc):
                    ids.append(int(self.AudioFilesList.item(row,6).text()))
                newid = max(ids)+1
            else: newid = 1
            num_channels, sample_rate, bit_depth, num_frames = get_wav_info(rawpath)
            row = self.AudioFilesList.rowCount()
            self.AudioFilesList.setRowCount(int(row + 1))
            self.AudioFilesList.setRowHeight(row,10)
            self.AudioFilesList.setItem(row,0,QTableWidgetItem(name))
            self.AudioFilesList.setItem(row,1,QTableWidgetItem(rawpath))
            self.AudioFilesList.setItem(row,2,QTableWidgetItem(str(num_channels)))
            self.AudioFilesList.setItem(row,3,QTableWidgetItem(str(sample_rate)))
            self.AudioFilesList.setItem(row,4,QTableWidgetItem(str(bit_depth)))
            self.AudioFilesList.setItem(row,5,QTableWidgetItem(str(num_frames)))
            self.AudioFilesList.setItem(row,6,QTableWidgetItem(str(newid)))
            self.updateSamplegrouplist()
        return None

    def remove_selected_audio_file(self):
        selected = self.AudioFilesList.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.AudioFilesList.removeRow(row)
            self.updateSamplegrouplist()

    def sgroupmoveup(self):
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if selected and self.ImporttabSampleGroupList.rowCount()>1:
            row = selected[0].row()
            if row > 0:
                for column in range(self.ImporttabSampleGroupList.columnCount()):
                    lowcell = self.ImporttabSampleGroupList.item(row, column)
                    hicell = self.ImporttabSampleGroupList.item(row-1, column)
                    if lowcell: lowcell=lowcell.text()
                    else: lowcell = ""
                    if hicell: hicell=hicell.text()
                    else: hicell = ""                   

                    self.ImporttabSampleGroupList.setItem(row,column,None)
                    self.ImporttabSampleGroupList.setItem(row,column,QTableWidgetItem(hicell))
                    self.ImporttabSampleGroupList.setItem(row-1,column,None)
                    self.ImporttabSampleGroupList.setItem(row-1,column,QTableWidgetItem(lowcell))
                self.ImporttabSampleGroupList.selectRow(row-1)
            self.updateSamplegrouplist()

    def sgroupmovedown(self):
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if selected and self.ImporttabSampleGroupList.rowCount()>1:
            row = selected[0].row()
            if row < self.ImporttabSampleGroupList.columnCount()+2:
                for column in range(self.ImporttabSampleGroupList.columnCount()):
                    lowcell = self.ImporttabSampleGroupList.item(row, column)
                    hicell = self.ImporttabSampleGroupList.item(row+1, column)
                    if lowcell: lowcell=lowcell.text()
                    else: lowcell = ""
                    if hicell: hicell=hicell.text()
                    else: hicell = ""                   

                    self.ImporttabSampleGroupList.setItem(row,column,None)
                    self.ImporttabSampleGroupList.setItem(row,column,QTableWidgetItem(hicell))
                    self.ImporttabSampleGroupList.setItem(row+1,column,None)
                    self.ImporttabSampleGroupList.setItem(row+1,column,QTableWidgetItem(lowcell))
                self.ImporttabSampleGroupList.selectRow(row+1)
            self.updateSamplegrouplist()
            self.update_sort_tab_sgroup_filter()

    def deletesamplegroup(self):
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.ImporttabSampleGroupList.removeRow(row)
            self.updateSamplegrouplist()
            self.update_sort_tab_sgroup_filter()


    def clonesamplegroup(self):
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if selected:
            rowc = self.ImporttabSampleGroupList.rowCount()
            if rowc > 0:
                ids = []
                for row in range(rowc):
                    item = self.ImporttabSampleGroupList.item(row, 1)
                    if item:
                        ids.append(int(item.text()))
                if ids:  
                    newid = max(ids) + 1
                else: newid = 1

            row = selected[0].row()
            self.ImporttabSampleGroupList.insertRow(row)
            for column in range(self.ImporttabSampleGroupList.columnCount()):
                cell = self.ImporttabSampleGroupList.item(row+1, column)
                if cell: cell=cell.text()
                else: cell = ""
                self.ImporttabSampleGroupList.setItem(row,column,None)
                self.ImporttabSampleGroupList.setItem(row,column,QTableWidgetItem(cell))
            self.ImporttabSampleGroupList.setItem(row,1,QTableWidgetItem(str(newid)))
        self.updateSamplegrouplist()

    def add_selected_audio_to_sgroup(self):
        selectedSGroup = self.ImporttabSampleGroupList.selectedIndexes()
        selectedAudio= self.AudioFilesList.selectedIndexes()
    
        if selectedAudio and selectedSGroup:
            SgroupRow = selectedSGroup[0].row()
            sgroupdata = self.ImporttabSampleGroupList.item(SgroupRow,2)
            if sgroupdata:
                sgroupdata = (string_to_list(sgroupdata.text()))
            else:
                sgroupdata = []
            ids = []
            for cell in selectedAudio:
                row = cell.row()
                id = str(self.AudioFilesList.item(row,6).text())
                ids.append(id)
            ids = list(set(ids + sgroupdata))
            textids = list_to_string(ids)
            self.ImporttabSampleGroupList.setItem(SgroupRow,2,None)
            self.ImporttabSampleGroupList.setItem(SgroupRow,2,QTableWidgetItem(textids))
        self.updateSamplegrouplist()
                
    def updateSamplegrouplist(self):
        selected = self.ImporttabSampleGroupList.selectedIndexes()
        if selected:
            sgrouprow = selected[0].row()
            sgroupdata = self.ImporttabSampleGroupList.item(sgrouprow,2)
            if sgroupdata:
                sgroupdata = (string_to_list(sgroupdata.text()))
            else:
                sgroupdata = []

            audioids = []
            for row in range(self.AudioFilesList.rowCount()):
                audioids.append([self.AudioFilesList.item(row,0).text(),self.AudioFilesList.item(row,6).text()])

            audioingroup = []
            for id in sgroupdata:
                for rec in audioids:
                    if rec[1] == id:
                        audioingroup.append(rec[0])
                        break

            self.SampleGroupContentsPreview.setRowCount(0)
            self.SampleGroupContentsPreview.setRowCount(len(audioingroup))
            i = 0
            for audio in audioingroup:
                self.SampleGroupContentsPreview.setItem(i,0,QTableWidgetItem(str(audio)))
                self.SampleGroupContentsPreview.setRowHeight(i,10)
                i += 1
                
    def updateSliceSGroupList(self):
        samplegroups = []
        rows = self.ImporttabSampleGroupList.rowCount()
        columns = self.ImporttabSampleGroupList.columnCount()
        self.SampleGroupSelection.setRowCount(rows)
        self.SampleGroupSelection.setColumnCount(columns+1)
        for row in range(rows):
            name = self.ImporttabSampleGroupList.item(row,0)
            id = self.ImporttabSampleGroupList.item(row,1)
            content = self.ImporttabSampleGroupList.item(row,2)
            if name:
                name = QTableWidgetItem(name.text())
                name.setFlags(name.flags() & ~Qt.ItemIsEditable)
                self.SampleGroupSelection.setItem(row,0,name)
            if id:
                self.SampleGroupSelection.setItem(row,1,QTableWidgetItem(id.text()))
            if content:
                self.SampleGroupSelection.setItem(row,2,QTableWidgetItem(content.text()))
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            self.SampleGroupSelection.setItem(row,3,checkbox_item)   
            self.SampleGroupSelection.setRowHeight(row,10)
        

    def updatetabs(self,index):
        if index == 0: #Import
            self.updateSamplegrouplist()
            
        elif index ==1: #Slice
            self.updateSliceSGroupList()


    def select_all_sample_groups(self):
        rows = self.SampleGroupSelection.rowCount()
        for row in range(rows):
            checkbox_item = self.SampleGroupSelection.item(row, 3)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Checked)
        
    def clear_all_sample_groups(self):
        rows = self.SampleGroupSelection.rowCount()
        for row in range(rows):
            checkbox_item = self.SampleGroupSelection.item(row, 3)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)

    def reset_table(self, table_widget):
        table_widget.clearContents()  # Clears all data but keeps headers
        table_widget.setRowCount(0)  # Resets the row count to 0

    def paste_clipboard_to_cutpoint(self):
        value = self.SampleCutpointInput.value()

        if self.AutoClipboardCheckbox.isChecked() and (value == 0 or value == None):
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text()
            if clipboard_text.isdigit():  # Check if the clipboard value is a number
                self.SampleCutpointInput.setValue(int(clipboard_text))

    def paste_clipboard_to_endinput(self):
        value = self.SampleEndInput.value()

        if self.AutoClipboardCheckbox.isChecked() and (value == 0 or value == None):
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text()
            if clipboard_text.isdigit():  # Check if the clipboard value is a number
                self.SampleEndInput.setValue(int(clipboard_text))

    def remove_sample_cut_data(self):
        selected_rows = self.Sample_Cut_Data_Table.selectionModel().selectedRows()
        for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
            self.Sample_Cut_Data_Table.removeRow(index.row())

    def load_audio_waveform(self, amplitudes, sample_rate):
        """
        Load and display a waveform from a list of amplitude values.

        :param amplitudes: List of amplitude values (e.g., from an audio file).
        :param sample_rate: The sample rate of the audio (in Hz).
        """
        # Convert the amplitude list to a numpy array
        samples = np.array(amplitudes, dtype=np.float32)

        # Normalize the samples to fit within the range -1 to +1
        if samples.max() > 1 or samples.min() < -1:
            samples = samples / np.max(np.abs(samples))

        # Generate the time axis
        time = np.linspace(0, len(samples) / sample_rate, num=len(samples))

        # Configure the PlotWidget
        
        # Plot the waveform
        self.AudioPreviewPplaceholder.clear()
        self.AudioPreviewPplaceholder.plot(time, samples, pen=pg.mkPen(color="blue", width=1))

    def update_sort_tab_sgroup_filter(self):
        """
        Populate the SortTabSGroupfilter combo box with sample groups
        from ImporttabSampleGroupList and set the default text.
        """
        self.SortTabSGroupfilter.clear()  # Clear existing items
        self.SortTabSGroupfilter.addItem("SGroup Filter")  # Add default text
        index = self.SortTabSGroupfilter.findText("SGroup Filter")
        if index != -1:
            self.SortTabSGroupfilter.model().item(index).setSizeHint(QtCore.QSize(0, 0))

        # Populate with sample group names
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            group_name_item = self.ImporttabSampleGroupList.item(row, 0)  # Column 0 contains the group name
            if group_name_item:
                self.SortTabSGroupfilter.addItem(group_name_item.text())

    def update_sort_tab_slice_list(self):
        """
        Update the SortTabSliceList to show slices from Sample_Cut_Data_Table
        that contain the selected sample group ID in SortTabSGroupfilter.
        """
        selected_group_name = self.SortTabSGroupfilter.currentText()

        # Clear the SortTabSliceList
        self.SortTabSliceList.clearContents()
        self.SortTabSliceList.setRowCount(0)

        # If "SGroup Filter" is selected, show all slices
        if selected_group_name == "SGroup Filter":
            self.SortTabSliceList.setRowCount(self.Sample_Cut_Data_Table.rowCount())
            for row in range(self.Sample_Cut_Data_Table.rowCount()):
                for col in range(self.Sample_Cut_Data_Table.columnCount()):
                    item = self.Sample_Cut_Data_Table.item(row, col)
                    if item:
                        self.SortTabSliceList.setItem(row, col, QTableWidgetItem(item.text()))
            return

        # Find the group ID corresponding to the selected group name
        selected_group_id = None
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            group_name_item = self.ImporttabSampleGroupList.item(row, 0)  # Column 0 contains the group name
            group_id_item = self.ImporttabSampleGroupList.item(row, 1)  # Column 1 contains the group ID
            if group_name_item and group_id_item and group_name_item.text() == selected_group_name:
                selected_group_id = group_id_item.text()
                break

        if not selected_group_id:
            return  # No matching group ID found, exit the method

        # Filter slices based on the selected sample group ID
        filtered_rows = []
        for row in range(self.Sample_Cut_Data_Table.rowCount()):
            sample_groups_item = self.Sample_Cut_Data_Table.item(row, 4)  # Column 4 contains sample groups (IDs)
            if sample_groups_item and selected_group_id in sample_groups_item.text():
                filtered_rows.append(row)

        # Populate SortTabSliceList with filtered rows
        self.SortTabSliceList.setRowCount(len(filtered_rows))
        for i, row in enumerate(filtered_rows):
            for col in range(self.Sample_Cut_Data_Table.columnCount()):
                item = self.Sample_Cut_Data_Table.item(row, col)
                if item:
                    self.SortTabSliceList.setItem(i, col, QTableWidgetItem(item.text()))

    def update_sort_preview_audio_select(self):
        """
        Update the SortPreviewAudioSelect combo box with audio clips
        from the selected sample group in SortTabSGroupfilter.
        """
        selected_group_name = self.SortTabSGroupfilter.currentText()

        # Clear the SortPreviewAudioSelect combo box
        self.SortPreviewAudioSelect.clear()

        # If "SGroup Filter" is selected, do not populate the combo box
        if selected_group_name == "SGroup Filter":
            self.SortPreviewAudioSelect.addItem("Select Audio Clip")
            return

        # Find the group ID corresponding to the selected group name
        selected_group_id = None
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            group_name_item = self.ImporttabSampleGroupList.item(row, 0)  # Column 0 contains the group name
            group_id_item = self.ImporttabSampleGroupList.item(row, 1)  # Column 1 contains the group ID
            if group_name_item and group_id_item and group_name_item.text() == selected_group_name:
                selected_group_id = group_id_item.text()
                break

        if not selected_group_id:
            self.SortPreviewAudioSelect.addItem("No Audio Clips Found")
            return  # No matching group ID found, exit the method

        # Find the row in ImporttabSampleGroupList corresponding to the group ID
        audio_file_ids = []
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            group_id_item = self.ImporttabSampleGroupList.item(row, 1)  # Column 1 contains the group ID
            group_content_item = self.ImporttabSampleGroupList.item(row, 2)  # Column 2 contains the audio file IDs
            if group_id_item and group_content_item and group_id_item.text() == selected_group_id:
                # Use string_to_list to get all audio file IDs in the group
                audio_file_ids = string_to_list(group_content_item.text())
                break

        # Find all audio clips in the AudioFilesList that match the audio file IDs
        audio_clips = []
        for row in range(self.AudioFilesList.rowCount()):
            audio_id_item = self.AudioFilesList.item(row, 6)  # Column 6 contains the audio file ID
            audio_name_item = self.AudioFilesList.item(row, 0)  # Column 0 contains the audio file name
            if audio_id_item and audio_name_item and audio_id_item.text() in audio_file_ids:
                audio_clips.append(audio_name_item.text())

        # Populate the SortPreviewAudioSelect combo box with audio clips
        if audio_clips:
            self.SortPreviewAudioSelect.addItems(audio_clips)
        else:
            self.SortPreviewAudioSelect.addItem("No Audio Clips Found")

    def update_waveform_preview(self):
        """
        Update the waveform display to show the selected audio file
        and the range specified in SortTabSliceList, and update pitch-related inputs and labels.
        """
        selected_rows = self.SortTabSliceList.selectionModel().selectedRows()
        if not selected_rows:
            self.FrequencyLabel.setText("Pitch Difference: N/A")
            self.NoteLabel.setText("Note: N/A")
            return  # No row selected

        selected_row = selected_rows[0].row()
        start_item = self.SortTabSliceList.item(selected_row, 1)
        end_item = self.SortTabSliceList.item(selected_row, 2)
        selected_audio = self.SortPreviewAudioSelect.currentText()

        if not (selected_audio and start_item and end_item):
            self.FrequencyLabel.setText("Pitch Difference: N/A")
            self.NoteLabel.setText("Note: N/A")
            return  # Missing data

        start_time = int(start_item.text())
        end_time = int(end_item.text())

        audio_file_path = None
        for row in range(self.AudioFilesList.rowCount()):
            audio_name_in_list = self.AudioFilesList.item(row, 0)
            audio_path_in_list = self.AudioFilesList.item(row, 1)
            if audio_name_in_list and audio_path_in_list and audio_name_in_list.text() == selected_audio:
                audio_file_path = audio_path_in_list.text()
                break

        if not audio_file_path:
            print("Audio file not found.")
            self.FrequencyLabel.setText("Pitch Difference: N/A")
            self.NoteLabel.setText("Note: N/A")
            return

        print(f"Loading audio file: {audio_file_path}")

        try:
            samples = read_wav_range_first_channel(audio_file_path, start_time, end_time)
            self.AudioPreviewPplaceholder.clear()
            time_axis = np.linspace(start_time, end_time, num=len(samples))
            maax = max([max(samples), abs(min(samples))])
            samples = [n / maax for n in samples]
            self.AudioPreviewPplaceholder.plot(time_axis, samples, pen="blue")

            # Detect pitch and update labels and inputs
            pitch_difference, note = detect_pitch(samples, samplerate=44100)  # Assuming 44100 Hz sample rate
            if pitch_difference is not None and note:
                self.FrequencyLabel.setText(f"Pitch Difference: {pitch_difference:.2f} cents")
                self.NoteLabel.setText(f"Note: {note}")

                # Update Octave and Note inputs
                note_name, octave = note[:-1], int(note[-1])  # Split note into name and octave
                self.NoteSelect.setCurrentText(note_name)
                self.OctaveSelect.setValue(octave)
            else:
                self.FrequencyLabel.setText("Pitch Difference: N/A")
                self.NoteLabel.setText("Note: N/A")

        except Exception as e:
            print(f"Error loading audio file: {e}")
            self.FrequencyLabel.setText("Pitch Difference: N/A")
            self.NoteLabel.setText("Note: N/A")
            
    def accept_note_config(self):
        """
        Add all audio files in the selected sample group to the ExportFinalTable,
        ensuring each row has a unique ID, and replacing any existing rows with the same Slice ID.
        """
        selected_rows = self.SortTabSliceList.selectionModel().selectedRows()
        if not selected_rows:
            print("No slice selected.")
            return

        selected_row = selected_rows[0].row()

        # Extract data from the selected slice
        slice_id_item = self.SortTabSliceList.item(selected_row, 0)  # Column 0: Slice ID
        sample_start_item = self.SortTabSliceList.item(selected_row, 1)  # Column 1: Sample Start
        sample_end_item = self.SortTabSliceList.item(selected_row, 2)  # Column 2: Sample End

        # Extract Note and Round Robin from Note Configuration
        note_item = self.NoteSelect.currentText()  # Note from the NoteSelect combo box
        octave = self.OctaveSelect.value()  # Octave from the OctaveSelect spin box
        midi_note = (octave * 12) + self.NoteSelect.currentIndex()  # Convert to MIDI note

        round_robin = self.RRSelect.value()  # Round Robin from the RRSelect spin box

        # Find the selected sample group name
        selected_group_name = self.SortTabSGroupfilter.currentText()
        if selected_group_name == "SGroup Filter":
            print("No sample group selected.")
            return

        # Find the group ID corresponding to the selected group name
        selected_group_id = None
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            group_name_item = self.ImporttabSampleGroupList.item(row, 0)  # Column 0: Group Name
            group_id_item = self.ImporttabSampleGroupList.item(row, 1)  # Column 1: Group ID
            if group_name_item and group_id_item and group_name_item.text() == selected_group_name:
                selected_group_id = group_id_item.text()
                break

        if not selected_group_id:
            print("Sample group not found.")
            return

        # Find all audio files in the group
        audio_file_ids = []
        for row in range(self.ImporttabSampleGroupList.rowCount()):
            group_id_item = self.ImporttabSampleGroupList.item(row, 1)  # Column 1: Group ID
            group_content_item = self.ImporttabSampleGroupList.item(row, 2)  # Column 2: Audio File IDs
            if group_id_item and group_content_item and group_id_item.text() == selected_group_id:
                audio_file_ids = string_to_list(group_content_item.text())
                break

        # Remove any existing rows with the same Slice ID
        slice_id = slice_id_item.text() if slice_id_item else ""
        rows_to_remove = []
        for row in range(self.ExportFinalTable.rowCount()):
            existing_slice_id_item = self.ExportFinalTable.item(row, 1)  # Column 1: Slice ID
            if existing_slice_id_item and existing_slice_id_item.text() == slice_id:
                rows_to_remove.append(row)

        # Remove rows in reverse order to avoid index shifting
        for row in reversed(rows_to_remove):
            self.ExportFinalTable.removeRow(row)

        # Determine the next available ID for the ExportFinalTable
        existing_ids = []
        for row in range(self.ExportFinalTable.rowCount()):
            id_item = self.ExportFinalTable.item(row, 0)  # Column 0: ID
            if id_item:
                existing_ids.append(int(id_item.text()))
        next_id = max(existing_ids) + 1 if existing_ids else 1

        # Add each audio file in the group to the ExportFinalTable
        for audio_file_id in audio_file_ids:
            for row in range(self.AudioFilesList.rowCount()):
                audio_id_item = self.AudioFilesList.item(row, 6)  # Column 6: Audio File ID
                audio_path_item = self.AudioFilesList.item(row, 1)  # Column 1: Audio File Path
                if audio_id_item and audio_path_item and audio_id_item.text() == audio_file_id:
                    # Add a new row to ExportFinalTable
                    row_position = self.ExportFinalTable.rowCount()
                    self.ExportFinalTable.insertRow(row_position)

                    # Populate the row
                    self.ExportFinalTable.setItem(row_position, 0, QTableWidgetItem(str(next_id)))  # Unique ID
                    self.ExportFinalTable.setItem(row_position, 1, QTableWidgetItem(slice_id))  # Slice ID
                    self.ExportFinalTable.setItem(row_position, 2, QTableWidgetItem(sample_start_item.text() if sample_start_item else ""))  # Sample Start
                    self.ExportFinalTable.setItem(row_position, 3, QTableWidgetItem(sample_end_item.text() if sample_end_item else ""))  # Sample End
                    self.ExportFinalTable.setItem(row_position, 4, QTableWidgetItem(audio_path_item.text()))  # Audio File Path
                    self.ExportFinalTable.setItem(row_position, 5, QTableWidgetItem(selected_group_name))  # Sample Group Name
                    self.ExportFinalTable.setItem(row_position, 6, QTableWidgetItem(str(midi_note)))  # MIDI Note
                    self.ExportFinalTable.setItem(row_position, 7, QTableWidgetItem(str(round_robin)))  # Round Robin

                    # Increment the ID for the next row
                    next_id += 1

    def accept_note_config_and_next(self):
        """
        Add all audio files in the selected sample group to the ExportFinalTable
        and select the next row in SortTabSliceList.
        """
        self.accept_note_config()  # Add the current data to the ExportFinalTable

        # Select the next row in SortTabSliceList
        selected_rows = self.SortTabSliceList.selectionModel().selectedRows()
        if not selected_rows:
            return

        current_row = selected_rows[0].row()
        next_row = current_row + 1

        if next_row < self.SortTabSliceList.rowCount():
            self.SortTabSliceList.selectRow(next_row)

    def play_audio_sample(self):
        """
        Play the selected audio sample using the Play button.
        """
        selected_audio = self.SortPreviewAudioSelect.currentText()
        selected_rows = self.SortTabSliceList.selectionModel().selectedRows()

        if not selected_audio or not selected_rows:
            print("No audio sample or range selected.")
            return

        selected_row = selected_rows[0].row()
        start_item = self.SortTabSliceList.item(selected_row, 1)
        end_item = self.SortTabSliceList.item(selected_row, 2)

        if not (start_item and end_item):
            print("Invalid start or end time.")
            return

        start_time = int(start_item.text())
        end_time = int(end_item.text())

        # Find the corresponding audio file path
        audio_file_path = None
        for row in range(self.AudioFilesList.rowCount()):
            audio_name_in_list = self.AudioFilesList.item(row, 0)
            audio_path_in_list = self.AudioFilesList.item(row, 1)
            if audio_name_in_list and audio_path_in_list and audio_name_in_list.text() == selected_audio:
                audio_file_path = audio_path_in_list.text()
                break

        if not audio_file_path:
            print("Audiofile not found.")
            return

        # Read the audio data for the selected range
        try:
            system_sample_rate = self.audio_output.device().preferredFormat().sampleRate()
            samples = read_wav_range_first_channel(audio_file_path, start_time, end_time)
            resampled_samples = fast_resample(samples, original_rate=44100, target_rate=system_sample_rate)
            vol = self.SortPreviewVolume.value()/10000

            play_wav_samples(resampled_samples, samplerate=system_sample_rate, volume=vol)

        except Exception as e:
            print(f"Error playing audio: {e}")

    def stop_audio_sample(self):
        stop_playback()

    def export_samples(self):
        """
        Export all cut samples into organized folders based on Sample Group, Round Robin, and Source Audio File Name,
        preserving the original audio format (sample rate, channels, and bit depth).
        """
        # Open a file dialog to select the export location
        export_dir = QFileDialog.getExistingDirectory(
            None,
            "Select Export Directory",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if not export_dir:
            print("Export canceled.")
            return

        # Get the project name
        project_name = os.path.splitext(os.path.basename(self.project_file_path))[0] if self.project_file_path else "UnnamedProject"

        # Get the total number of samples to export
        total_samples = self.ExportFinalTable.rowCount()

        # Create a progress dialog
        progress_dialog = QProgressDialog("Exporting samples...", "Cancel", 0, total_samples)
        progress_dialog.setWindowTitle("Export Progress")
        progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress_dialog.setMinimumDuration(0)

        # Iterate through the ExportFinalTable to organize and export files
        for row in range(total_samples):
            # Check if the user canceled the operation
            if progress_dialog.wasCanceled():
                print("Export canceled by user.")
                break

            # Update the progress dialog
            progress_dialog.setValue(row)
            QApplication.processEvents()  # Allow the UI to update

            # Extract data from the table
            sample_group_name = self.ExportFinalTable.item(row, 5).text()  # Column 5: Sample Group Name
            round_robin = self.ExportFinalTable.item(row, 7).text()  # Column 7: Round Robin
            midi_note = self.ExportFinalTable.item(row, 6).text()  # Column 6: MIDI Note
            audio_file_path = self.ExportFinalTable.item(row, 4).text()  # Column 4: Audio File Path
            slice_start = int(self.ExportFinalTable.item(row, 2).text())  # Column 2: Sample Start
            slice_end = int(self.ExportFinalTable.item(row, 3).text())  # Column 3: Sample End

            # Retrieve the Name value from the AudioFilesList table
            source_audio_name = None
            for audio_row in range(self.AudioFilesList.rowCount()):
                audio_path_item = self.AudioFilesList.item(audio_row, 1)  # Column 1: Audio File Path
                audio_name_item = self.AudioFilesList.item(audio_row, 0)  # Column 0: Name
                if audio_path_item and audio_path_item.text() == audio_file_path:
                    source_audio_name = audio_name_item.text()
                    break

            if not source_audio_name:
                print(f"Warning: Could not find Name for audio file {audio_file_path}. Skipping.")
                continue

            # Create the folder structure
            group_folder = os.path.join(export_dir, sample_group_name)
            round_robin_folder = os.path.join(group_folder, f"RoundRobin_{round_robin}")
            source_audio_folder = os.path.join(round_robin_folder, source_audio_name)
            os.makedirs(source_audio_folder, exist_ok=True)

            # Generate the output file name
            note_name = NOTE_NAMES[int(midi_note) % 12]
            octave = (int(midi_note) // 12) - 1
            note_str = f"{note_name}{octave}"
            output_file_name = f"{project_name} - {sample_group_name} - {note_str} - {round_robin} - {source_audio_name}.wav"
            output_file_path = os.path.join(source_audio_folder, output_file_name)

            # Extract the audio range and save to the output file
            try:
                extract_audio_range(audio_file_path, slice_start, slice_end, output_file_path)
                print(f"Exported: {output_file_path}")
            except Exception as e:
                print(f"Error exporting {audio_file_path}: {e}")

        # Finalize the progress dialog
        progress_dialog.setValue(total_samples)
        print(f"Export completed. Files saved to {export_dir}")
        
def read_wav_range_first_channel(filename, start_sample, end_sample):
    """
    Reads a range of samples from a WAV file (only the first channel) and returns the values as a list.
    Supports 8-bit, 16-bit, and 24-bit PCM WAV files.

    Args:
        filename (str): Path to the WAV file.
        start_sample (int): The index of the first sample to read (0-based).
        end_sample (int): The index of the last sample to read (exclusive).

    Returns:
        List[int]: List of sample values from the first channel.
    """
    first_channel_samples = []

    with wave.open(filename, 'rb') as wav_file:
        n_channels = wav_file.getnchannels()
        sampwidth = wav_file.getsampwidth()  # bytes per sample
        n_frames = wav_file.getnframes()

        if start_sample < 0 or end_sample > n_frames or start_sample >= end_sample:
            raise ValueError("Invalid start_sample or end_sample range.")

        wav_file.setpos(start_sample)
        frames_to_read = end_sample - start_sample
        raw_data = wav_file.readframes(frames_to_read)

        if sampwidth == 1:
            # 8-bit PCM is unsigned
            fmt = f'{frames_to_read * n_channels}B'
            unpacked_data = struct.unpack(fmt, raw_data)
            first_channel_samples = list(unpacked_data[::n_channels])

        elif sampwidth == 2:
            # 16-bit PCM is signed
            fmt = f'<{frames_to_read * n_channels}h'
            unpacked_data = struct.unpack(fmt, raw_data)
            first_channel_samples = list(unpacked_data[::n_channels])

        elif sampwidth == 3:
            # 24-bit PCM: manually unpack
            first_channel_samples = []
            bytes_per_frame = n_channels * 3
            for frame_index in range(frames_to_read):
                frame_start = frame_index * bytes_per_frame
                first_channel_bytes = raw_data[frame_start:frame_start+3]

                # 24-bit little-endian to integer
                as_int = int.from_bytes(first_channel_bytes, byteorder='little', signed=True)
                first_channel_samples.append(as_int)

        else:
            raise ValueError(f"Unsupported sample width: {sampwidth} bytes")

    return first_channel_samples



def fast_resample(samples, original_rate, target_rate):
    """
    Fast and low-quality resampling: just picks samples at scaled positions.
    
    Args:
        samples (list or np.array): Input samples.
        original_rate (int): Original sample rate.
        target_rate (int): Target sample rate.

    Returns:
        np.array: Resampled audio samples.
    """
    samples = np.asarray(samples)
    ratio = target_rate / original_rate
    n_target_samples = int(len(samples) * ratio)

    indices = np.linspace(0, len(samples) - 1, n_target_samples).astype(int)
    resampled = samples[indices]

    return resampled


def get_wav_info(file_path: str) -> tuple[int, int, int, int]:
    with contextlib.closing(wave.open(file_path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()  # in bytes per sample
        num_frames = wf.getnframes()

        bit_depth = sample_width * 8

        return num_channels, sample_rate, bit_depth, num_frames

def list_to_string(lst, delimiter=','):
    return delimiter.join(map(str, lst))

def string_to_list(s, delimiter=','):
    return s.split(delimiter)

def play_wav_samples(samples, samplerate, volume=1.0):
    """
    Plays the given audio samples at the given sample rate using non-blocking playback.
    
    Args:
        samples (list or np.array): Audio samples to play (mono).
        samplerate (int): Sample rate for playback.
        volume (float): Volume level from 0.0 (mute) to 1.0 (full volume).
    """
    global _current_stream

    # Stop any existing playback
    stop_playback()

    # Convert samples to numpy array
    samples = np.asarray(samples)

    # Normalize if needed
    if samples.dtype != np.float32:
        if samples.dtype == np.int8:
            samples = (samples.astype(np.float32) - 128) / 128.0
        elif samples.dtype == np.uint8:
            samples = (samples.astype(np.float32) - 128) / 128.0
        elif samples.dtype == np.int16:
            samples = samples.astype(np.float32) / 32768.0
        elif samples.dtype == np.int32:
            samples = samples.astype(np.float32) / 2147483648.0
        else:
            # Assuming 24-bit
            samples = samples.astype(np.float32) / (2 ** 23)

    # Apply volume (dB scaling)
    if volume <= 0.0:
        gain = 0.0  # mute
    else:
        gain_db = 20.0 * np.log10(volume)
        gain = 10.0 ** (gain_db / 20.0)

    samples *= gain

    # Make sure it's shaped as (frames, channels)
    samples = samples.reshape(-1, 1)

    # Iterator over samples
    sample_iter = iter(samples)

    def callback(outdata, frames, time, status):
        try:
            for i in range(frames):
                outdata[i] = next(sample_iter)
        except StopIteration:
            raise sd.CallbackStop

    _current_stream = sd.OutputStream(
        samplerate=samplerate,
        channels=1,
        dtype='float32',
        callback=callback
    )
    _current_stream.start()

def stop_playback():
    """
    Stops any currently playing audio.
    """
    global _current_stream
    if _current_stream is not None:
        _current_stream.stop()
        _current_stream.close()
        _current_stream = None



def get_note_frequency(midi_note):
    """
    Calculates the frequency of a note based on its MIDI number using A440 tuning.
    
    Args:
        midi_note (int): The MIDI note number.
        
    Returns:
        float: The frequency of the note in Hz.
    """
    return 440.0 * 2 ** ((midi_note - 69) / 12.0)

def detect_pitch(samples, samplerate):
    """
    Detects the fundamental frequency (pitch) of the given audio samples using scipy.signal.correlate,
    and returns the pitch difference in cents from the closest note.

    Args:
        samples (np.array): Audio samples (mono, normalized).
        samplerate (int): Sample rate of the audio.

    Returns:
        tuple: Detected pitch difference in cents, and the corresponding note name (e.g., 'A4')
    """
    samples = np.asarray(samples)

    # Remove DC offset
    samples = samples - np.mean(samples)

    # Use scipy.signal.correlate for more efficient autocorrelation
    corr = correlate(samples, samples, mode='full')
    corr = corr[len(corr)//2:]  # Keep only second half (non-negative lags)

    # Find first real peak
    d = np.diff(corr)
    start = np.nonzero(d > 0)[0]
    if len(start) == 0:
        return None, None  # No positive slope, no pitch
    start = start[0]

    peak = np.argmax(corr[start:]) + start
    period = peak

    if period == 0:
        return None, None

    frequency = samplerate / period

    # Convert frequency to nearest MIDI note
    midi_note = 69 + 12 * np.log2(frequency / 440.0)
    midi_note = round(midi_note)
    
    # Get the note name and frequency
    note_name = NOTE_NAMES[midi_note % 12]
    octave = (midi_note // 12) - 1
    note_str = f"{note_name}{octave}"
    
    # Calculate the frequency of the note dynamically
    note_freq = get_note_frequency(midi_note)

    # Calculate the difference in cents
    cents_difference = 1200 * np.log2(frequency / note_freq)

    return cents_difference, note_str

import wave
import shutil

def extract_audio_range(input_file, start_idx, end_idx, output_file):
    """
    Extract a range of audio from an input file and save it to a new output file.
    
    Args:
        input_file (str): Path to the input audio file.
        start_idx (int): The start sample index.
        end_idx (int): The end sample index.
        output_file (str): Path where the new audio file should be saved.
    """
    with wave.open(input_file, 'rb') as in_wav:
        # Get parameters from the original file (channel, sample width, etc.)
        params = in_wav.getparams()

        # Ensure the indices are within the file's length
        num_samples = params.nframes
        if start_idx < 0 or end_idx > num_samples or start_idx >= end_idx:
            raise ValueError("Invalid start or end index")

        # Set the position to the start index
        in_wav.setpos(start_idx)

        # Read the specified range of audio frames
        audio_data = in_wav.readframes(end_idx - start_idx)

        # Open the output file in write-binary mode
        with wave.open(output_file, 'wb') as out_wav:
            # Set the same parameters (no conversion to keep original data)
            out_wav.setparams(params)

            # Write the extracted audio data to the new file
            out_wav.writeframes(audio_data)

    print(f"Audio range extracted and saved to: {output_file}")
