#! /usr/bin/python
import sys
import os
import re
import json
from os.path import exists
from time import strftime, gmtime
from PySide2 import QtCore, QtGui
from PySide2.QtCore import Qt, QSize, QProcess, QByteArray, QTimer, QProcessEnvironment
from PySide2.QtWidgets import (
    QApplication,
    QSizePolicy,
    QSpacerItem,
    QScrollArea,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QListWidget,
    QWidget,
    QAction,
    QDialog,
    QStackedLayout,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QTabWidget,
    QLineEdit,
    QCheckBox,
    QRadioButton,
    QComboBox,
    QPlainTextEdit,
    QTableView,
    QProgressBar
)

class QSelectModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super(QSelectModel, self).__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # Look up the key by header index.
            column = index.column()
            column_key = self._headers[column]
            return self._data[index.row()][column_key]

    def rowCount(self, parent=QtCore.QModelIndex()):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        # The length of our headers.
        return len(self._headers)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

            if orientation == Qt.Vertical:
                return str(section)

class CaptureModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super(CaptureModel, self).__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # Look up the key by header index.
            column = index.column()
            column_key = self._headers[column]
            return self._data[index.row()][column_key]

    def rowCount(self, parent=QtCore.QModelIndex()):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        # The length of our headers.
        return len(self._headers)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

            if orientation == Qt.Vertical:
                return str(section)

    def appendRow(self, k, u, q, o, f):
        if self._data == None:
            self._data = dict(cid=k, url=u, quality=q, option=o, filename=f)
        else:
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
            self._data.append(dict(cid=k, url=u, quality=q, option=o, filename=f))
            self.endInsertRows()
        self.save()

    def removeRow(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._data[row]
        self.endRemoveRows()
        self.save()

    def save(self):
        with open("captures.json", "w") as f:
            data = json.dump(self._data, f)

class DownloadModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super(DownloadModel, self).__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # Look up the key by header index.
            column = index.column()
            column_key = self._headers[column]
            return self._data[index.row()][column_key]

    def rowCount(self, parent=QtCore.QModelIndex()):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        # The length of our headers.
        return len(self._headers)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

            if orientation == Qt.Vertical:
                return str(section)

    def appendRow(self, k, u, o, f):
        if self._data == None:
            self._data = dict(cid=k, url=u, option=o, filename=f)
        else:
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
            self._data.append(dict(cid=k, url=u, option=o, filename=f))
            self.endInsertRows()
        self.save()

    def removeRow(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._data[row]
        self.endRemoveRows()
        self.save()

    def save(self):
        with open("downloads.json", "w") as f:
            data = json.dump(self._data, f)

# A regular expression, to extract the % complete.
progress_re = re.compile("(\d+).(\d+)%")
video_re = re.compile('Detected (.*)$')
#5.07 / 324 MiB
size_re = re.compile("[0-9]+.[0-9][0-9] [MGK]iB / [0-9]+.[0-9][0-9] [MGK]iB")
alt_size_re = re.compile("[0-9]+.[0-9][0-9] / [0-9]+.[0-9][0-9] [MGK]iB")
time_re = re.compile("[0-9][0-9]:[0-9][0-9] > [0-9][0-9]:[0-9][0-9]")
mbspeed_re = re.compile("[0-9].[0-9][0-9] [MGK]iB/s")
seg_re = re.compile("[0-9]+/[0-9]+")
segspeed_re = re.compile("[0-9]+.[0-9]+ SEG/s")
dfilename_re = re.compile("vsd_\S+")
init_re = re.compile("INFO waiting for CTRL(.*)C signal")

def simple_percent_parser(output):
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    m = progress_re.search(output)
    if m:
        pc_complete = m.group(1)
        return int(pc_complete)

def video_link_locator(output):
    m = video_re.search(output)
    if m:
        videoURL = m.group()
        return videoURL

def download_size(output):
    m = size_re.search(output)
    a = alt_size_re.search(output)
    if m:
        pc_complete = m.group()
        return pc_complete
    if a:
        pc_complete = a.group()
        return pc_complete
    
def download_time(output):
    m = time_re.search(output)
    if m:
        pc_complete = m.group()
        return pc_complete

def download_mbspeed(output):
    m = mbspeed_re.search(output)
    if m:
        pc_complete = m.group()
        return pc_complete

def download_seg(output):
    m = seg_re.search(output)
    if m:
        pc_complete = m.group()
        return pc_complete

def download_segpeed(output):
    m = segspeed_re.search(output)
    if m:
        pc_complete = m.group()
        return pc_complete

def download_filename(output):
    m = dfilename_re.search(output)
    if m:
        pc_complete = m.group()
        return pc_complete

def capture_init(output):
    m = init_re.search(output)
    if m:
        return True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.captures = []
        self.downloads = []
        self.links = []
        self.p = None

        self.loadCaptures()
        cdump = json.dumps(self.captures)
        cd = json.loads(cdump)

        self.loadDownloads()
        #self.downloads = Global_Downloads
        ddump = json.dumps(self.downloads)
        dd = json.loads(ddump)

        cheaders = ['url', 'quality', 'option', 'filename']
        self.capturemodel = CaptureModel(cd, cheaders)

        dheaders = ['url', 'option', 'filename']
        self.downloadmodel = DownloadModel(dd, dheaders)

        self.setWindowTitle("VSD GUI")

        preferences_action = QAction("&Preferences", self)
        preferences_action.triggered.connect(lambda: self.loadPreferences())

        menu = self.menuBar()

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(preferences_action)

        self.resize(QSize(1000, 500))
        self.layout = QVBoxLayout()
        tabs = QTabWidget(self)
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.North)
        tabs.setMovable(True)

        tab1 = QWidget(self)
        tab1.layout1 = QVBoxLayout()
        tab1.layout2 = QHBoxLayout()
        tab1.layout3 = QHBoxLayout()
        tab1.setLayout(tab1.layout1)

        row1 = QWidget()
        tab1.layout1.addWidget(row1)
        row1.setLayout(tab1.layout2)

        captureLabel = QLabel("URLs to be Captured")
        tab1.layout2.addWidget(captureLabel)

        self.CaptureRefreshButton = QPushButton("Refresh")
        tab1.layout2.addWidget(self.CaptureRefreshButton)
        self.CaptureRefreshButton.clicked.connect(lambda: self.capturerefresh())
        self.CaptureRefreshButton.setFixedSize(100, 30)

        self.captureView = QTableView()
        self.captureView.setShowGrid(False)
        tab1.layout1.addWidget(self.captureView)
        self.captureView.setModel(self.capturemodel)
        self.captureView.setColumnWidth(0, 450)
        self.captureView.setColumnWidth(3, 150)
        self.captureView.resizeColumnsToContents()

        row2 = QWidget()
        tab1.layout1.addWidget(row2)
        row2.setLayout(tab1.layout3)

        downloadLabel = QLabel("URLs to be Downloaded")
        tab1.layout3.addWidget(downloadLabel)

        self.DownloadRefreshButton = QPushButton("Refresh")
        tab1.layout3.addWidget(self.DownloadRefreshButton)
        self.DownloadRefreshButton.clicked.connect(lambda: self.downloadrefresh())
        self.DownloadRefreshButton.setFixedSize(100, 30)

        self.downloadView = QTableView()
        self.downloadView.setShowGrid(False)
        tab1.layout1.addWidget(self.downloadView)
        self.downloadView.setModel(self.downloadmodel)
        self.downloadView.setColumnWidth(0, 450)
        self.downloadView.setColumnWidth(2, 150)
        self.downloadView.resizeColumnsToContents()

        self.StartButton = QPushButton("Start")
        tab1.layout1.addWidget(self.StartButton)

        self.progressBar1 = QProgressBar()
        self.progressBar1.minimum = 1
        self.progressBar1.maximum = 100
        tab1.layout1.addWidget(self.progressBar1)
        self.progressBar1.setVisible(False)

        tab1.layout1.setAlignment(Qt.AlignTop)

        tab2 = QWidget()
        tab2.layout = QGridLayout()
        tab2.layout2 = QGridLayout()
        tab2.layout3 = QHBoxLayout()
        tab2.layout4 = QHBoxLayout()
        tab2.layout5 = QHBoxLayout()
        tab2.layout6 = QHBoxLayout()
        tab2.layout7 = QVBoxLayout()
        tab2.layout8 = QVBoxLayout()
        tab2.setLayout(tab2.layout)

        capturegroupbox1 = QWidget()
        tab2.layout.addWidget(capturegroupbox1, 0, 0)
        capturegroupbox1.setLayout(tab2.layout2)

        capturerow1 = QWidget()
        tab2.layout2.addWidget(capturerow1, 0, 0)
        capturerow1.setLayout(tab2.layout3)
        captureLabel2 = QLabel("URL to Capture:")
        tab2.layout3.addWidget(captureLabel2)
        self.captureText2 = QLineEdit()
        tab2.layout3.addWidget(self.captureText2)

        capturerow2 = QWidget()
        tab2.layout2.addWidget(capturerow2, 1, 0)
        capturerow2.setLayout(tab2.layout4)
        self.autoDownload = QCheckBox("Auto Download after capture")
        tab2.layout4.addWidget(self.autoDownload)
        self.autoDownload.setCheckState(Qt.Checked)
        self.autoDownload.stateChanged.connect(self.ADstate)
        self.downloadQuality = QComboBox()
        tab2.layout4.addWidget(self.downloadQuality)
        self.downloadQuality.addItems(["Select", "Playlist", "Lowest", "Highest"])

        capturerow3 = QWidget()
        tab2.layout2.addWidget(capturerow3, 2, 0)
        capturerow3.setLayout(tab2.layout5)
        self.captureparseOutput = QCheckBox("After Processing:")
        tab2.layout5.addWidget(self.captureparseOutput)
        self.captureparseOutput.setCheckState(Qt.Unchecked)
        self.captureMuxOutput = QRadioButton("Send to ffmpeg")
        tab2.layout5.addWidget(self.captureMuxOutput)
        self.captureMuxOutput.setChecked(True)
        self.captureMuxOutput.setEnabled(False)
        self.capturerenameOutput = QRadioButton("Rename at completion")
        tab2.layout5.addWidget(self.capturerenameOutput)
        self.capturerenameOutput.setChecked(False)
        self.capturerenameOutput.setEnabled(False)
        filenameLabel = QLabel("As:")
        tab2.layout5.addWidget(filenameLabel)
        self.captureparseOutput.stateChanged.connect(self.captureParsestate)
        self.captureparseName = QLineEdit()
        tab2.layout5.addWidget(self.captureparseName)
        self.captureparseName.setEnabled(False)

        capturerow4 = QWidget()
        tab2.layout.addWidget(capturerow4, 1, 0)
        capturerow4.setLayout(tab2.layout6)
        self.captureQueueView = QTableView()
        self.captureQueueView.setShowGrid(False)
        tab2.layout6.addWidget(self.captureQueueView)
        self.captureQueueView.setModel(self.capturemodel)
        self.captureQueueView.setColumnWidth(0, 450)
        self.captureQueueView.setColumnWidth(3, 150)
        self.captureQueueView.resizeColumnsToContents()
        self.captureQueueView.setSelectionBehavior(QTableView.SelectRows)
        self.captureQueueView.doubleClicked.connect(lambda: self.selectcapture())

        capturebuttonbox1 = QWidget()
        tab2.layout.addWidget(capturebuttonbox1, 0, 1)
        capturebuttonbox1.setLayout(tab2.layout7)
        self.CaptureStartButton = QPushButton("Capture")
        tab2.layout7.addWidget(self.CaptureStartButton)
        self.CaptureStartButton.clicked.connect(lambda: self.CaptureNow())
        self.CaptureStartButton.setFixedSize(150, 25)
        self.CaptureCancelButton = QPushButton("Cancel")
        tab2.layout7.addWidget(self.CaptureCancelButton)
        self.CaptureCancelButton.clicked.connect(lambda: self.p.kill())
        self.CaptureCancelButton.setFixedSize(150, 25)
        self.CaptureCancelButton.setEnabled(False)
        CaptureClearButton = QPushButton("Clear")
        tab2.layout7.addWidget(CaptureClearButton)
        CaptureClearButton.clicked.connect(lambda: self.clearCapture())
        CaptureClearButton.setFixedSize(150, 25)

        capturebuttonbox2 = QWidget()
        tab2.layout.addWidget(capturebuttonbox2, 1, 1)
        capturebuttonbox2.setLayout(tab2.layout8)
        self.CaptureAddButton = QPushButton("Add to Queue")
        tab2.layout8.addWidget(self.CaptureAddButton)
        self.CaptureAddButton.clicked.connect(lambda: self.addcapture())
        self.CaptureAddButton.setFixedSize(150, 25)
        CaptureRemoveButton = QPushButton("Remove from Queue")
        tab2.layout8.addWidget(CaptureRemoveButton)
        CaptureRemoveButton.clicked.connect(lambda: self.deletecapture())
        CaptureRemoveButton.setFixedSize(150, 25)

        self.progressBar2 = QProgressBar()
        self.progressBar2.minimum = 1
        self.progressBar2.maximum = 100
        tab2.layout.addWidget(self.progressBar2, 2, 0)
        self.progressBar2.setVisible(False)

        tab2.layout.setAlignment(Qt.AlignTop)
        tab2.layout2.setAlignment(Qt.AlignTop)
        tab2.layout3.setAlignment(Qt.AlignTop)
        tab2.layout4.setAlignment(Qt.AlignTop)
        tab2.layout5.setAlignment(Qt.AlignTop)
        tab2.layout6.setAlignment(Qt.AlignTop)
        tab2.layout7.setAlignment(Qt.AlignTop)
        tab2.layout8.setAlignment(Qt.AlignTop)

        tab3 = QWidget()
        tab3.layout = QGridLayout()
        tab3.layout2 = QGridLayout()
        tab3.layout3 = QHBoxLayout()
        tab3.layout4 = QHBoxLayout()
        tab3.layout5 = QVBoxLayout()
        tab3.layout6 = QVBoxLayout()
        tab3.layout7 = QVBoxLayout()
        tab3.layout8 = QVBoxLayout()
        tab3.setLayout(tab3.layout)

        downloadgroupbox1 = QWidget()
        tab3.layout.addWidget(downloadgroupbox1, 0, 0)
        downloadgroupbox1.setLayout(tab3.layout2)
        downloadgroupbox1.setContentsMargins(0, 0, 0, 0)

        downloadrow1 = QWidget()
        tab3.layout2.addWidget(downloadrow1)
        downloadrow1.setLayout(tab3.layout3)
        downloadrow1.setContentsMargins(0, 0, 0, 0)
        downloadLabel2 = QLabel("URL to Download from:")
        tab3.layout3.addWidget(downloadLabel2)
        self.downloadText2 = QLineEdit()
        tab3.layout3.addWidget(self.downloadText2)

        downloadrow2 = QWidget()
        tab3.layout2.addWidget(downloadrow2, 1, 0)
        downloadrow2.setLayout(tab3.layout4)
        downloadrow2.setContentsMargins(0, 0, 0, 0)
        self.downloadparseOutput = QCheckBox("After Processing:")
        tab3.layout4.addWidget(self.downloadparseOutput)
        self.downloadparseOutput.setCheckState(Qt.Unchecked)
        self.downloadMuxOutput = QRadioButton("Send to ffmpeg")
        tab3.layout4.addWidget(self.downloadMuxOutput)
        self.downloadMuxOutput.setChecked(True)
        self.downloadMuxOutput.setEnabled(False)
        self.downloadrenameOutput = QRadioButton("Rename at completion")
        tab3.layout4.addWidget(self.downloadrenameOutput)
        self.downloadrenameOutput.setChecked(False)
        self.downloadrenameOutput.setEnabled(False)
        filenameLabel = QLabel("As:")
        tab3.layout4.addWidget(filenameLabel)
        self.downloadparseName = QLineEdit()
        tab3.layout4.addWidget(self.downloadparseName)
        self.downloadparseName.setEnabled(False)
        self.downloadparseOutput.stateChanged.connect(self.downloadParsestate)

        downloadrow3 = QWidget()
        tab3.layout.addWidget(downloadrow3, 1, 0)
        downloadrow3.setLayout(tab3.layout5)
        downloadrow3.setContentsMargins(0, 0, 0, 0)
        self.downloadQueueView = QTableView()
        self.downloadQueueView.setShowGrid(False)
        tab3.layout5.addWidget(self.downloadQueueView)
        self.downloadQueueView.setModel(self.downloadmodel)
        self.downloadQueueView.setColumnWidth(0, 450)
        self.downloadQueueView.setColumnWidth(3, 150)
        self.downloadQueueView.resizeColumnsToContents()
        self.downloadQueueView.setSelectionBehavior(QTableView.SelectRows)
        self.downloadQueueView.doubleClicked.connect(lambda: self.selectdownload())

        downloadbuttonbox1 = QWidget()
        tab3.layout.addWidget(downloadbuttonbox1, 0, 1)
        downloadbuttonbox1.setLayout(tab3.layout6)
        downloadbuttonbox1.setContentsMargins(0, 0, 0, 0)
        self.DownloadStartButton = QPushButton("Download")
        tab3.layout6.addWidget(self.DownloadStartButton)
        self.DownloadStartButton.clicked.connect(
            lambda: self.DownloadNow())
        self.DownloadStartButton.setFixedSize(150, 25)
        self.DownloadCancelButton = QPushButton("Cancel")
        tab3.layout6.addWidget(self.DownloadCancelButton)
        self.DownloadCancelButton.clicked.connect(lambda: self.p.terminate())
        self.DownloadCancelButton.setFixedSize(150, 25)
        self.DownloadCancelButton.setEnabled(False)
        self.DownloadClearButton = QPushButton("Clear")
        tab3.layout6.addWidget(self.DownloadClearButton)
        self.DownloadClearButton.clicked.connect(lambda: self.clearDownload())
        self.DownloadClearButton.setFixedSize(150, 25)

        downloadbuttonbox2 = QWidget()
        tab3.layout.addWidget(downloadbuttonbox2, 1, 1)
        downloadbuttonbox2.setLayout(tab3.layout7)
        downloadbuttonbox2.setContentsMargins(0, 0, 0, 0)
        DownloadAddButton = QPushButton("Add to Queue")
        tab3.layout7.addWidget(DownloadAddButton)
        DownloadAddButton.clicked.connect(lambda: self.addDownload())
        DownloadAddButton.setFixedSize(150, 25)
        DownloadRemoveButton = QPushButton("Remove from Queue")
        tab3.layout7.addWidget(DownloadRemoveButton)
        DownloadRemoveButton.clicked.connect(lambda: self.deletedownload())
        DownloadRemoveButton.setFixedSize(150, 25)

        self.downloadtimedsp = QLineEdit()
        tab3.layout7.addWidget(self.downloadtimedsp)
        self.downloadtimedsp.setFixedWidth(150)
        self.downloadtimedsp.setAlignment(Qt.AlignCenter)
        self.downloadtimedsp.setEnabled(False)
        self.downloadtimedsp.setVisible(False)

        self.downloadsizedsp = QLineEdit()
        tab3.layout7.addWidget(self.downloadsizedsp)
        self.downloadsizedsp.setFixedWidth(150)
        self.downloadsizedsp.setAlignment(Qt.AlignCenter)
        self.downloadsizedsp.setEnabled(False)
        self.downloadsizedsp.setVisible(False)

        self.downloadmbspeeddsp = QLineEdit()
        tab3.layout7.addWidget(self.downloadmbspeeddsp)
        self.downloadmbspeeddsp.setFixedWidth(150)
        self.downloadmbspeeddsp.setAlignment(Qt.AlignCenter)
        self.downloadmbspeeddsp.setEnabled(False)
        self.downloadmbspeeddsp.setVisible(False)

        self.downloadsegsdsp = QLineEdit()
        tab3.layout7.addWidget(self.downloadsegsdsp)
        self.downloadsegsdsp.setFixedWidth(150)
        self.downloadsegsdsp.setAlignment(Qt.AlignCenter)
        self.downloadsegsdsp.setEnabled(False)
        self.downloadsegsdsp.setVisible(False)

        self.downloadsegspeeddsp = QLineEdit()
        tab3.layout7.addWidget(self.downloadsegspeeddsp)
        self.downloadsegspeeddsp.setFixedWidth(150)
        self.downloadsegspeeddsp.setAlignment(Qt.AlignCenter)
        self.downloadsegspeeddsp.setEnabled(False)
        self.downloadsegspeeddsp.setVisible(False)

        self.progressBar3 = QProgressBar()
        self.progressBar3.minimum = 1
        self.progressBar3.maximum = 100
        tab3.layout.addWidget(self.progressBar3, 2, 0)
        self.progressBar3.setVisible(False)

        tab3.layout.setAlignment(Qt.AlignTop)
        tab3.layout2.setAlignment(Qt.AlignTop)
        tab3.layout3.setAlignment(Qt.AlignTop)
        tab3.layout4.setAlignment(Qt.AlignTop)
        tab3.layout5.setAlignment(Qt.AlignTop)
        tab3.layout6.setAlignment(Qt.AlignTop)
        tab3.layout7.setAlignment(Qt.AlignTop)

        tab4 = QWidget()
        tab4.layout = QGridLayout()
        tab4.setLayout(tab4.layout)
        self.statustext = QPlainTextEdit()
        self.statustext.setReadOnly(True)
        tab4.layout.addWidget(self.statustext, 0, 0)

        self.progressBar4 = QProgressBar()
        self.progressBar4.minimum = 1
        self.progressBar4.maximum = 100
        tab4.layout.addWidget(self.progressBar4, 1, 0)
        self.progressBar4.setVisible(False)

        tab4.layout.setAlignment(Qt.AlignTop)

        tabs.addTab(tab1, "Queue")
        tabs.addTab(tab2, "Capture")
        tabs.addTab(tab3, "Download")
        tabs.addTab(tab4, "Status")

        self.setCentralWidget(tabs)

        #self.show()

    def clearCapture(self):
        self.captureText2.setText("")
        self.captureparseName.setText("")

    def clearDownload(self):
        self.downloadText2.setText("")
        self.downloadparseName.setText("")

    def capturerefresh(self):
        self.capturemodel.layoutAboutToBeChanged.emit()
        self.loadCaptures()
        ddump = json.dumps(self.downloads)
        cd = json.loads(ddump)
        cheaders = ['url', 'quality', 'option', 'filename']
        self.capturemodel = CaptureModel(cd, cheaders)
        self.captureQueueView.setModel(self.capturemodel)
        self.captureView.setModel(self.downloadmodel)
        self.capturemodel.layoutChanged.emit()

    def downloadrefresh(self):
        self.downloadmodel.layoutAboutToBeChanged.emit()
        self.loadDownloads()
        ddump = json.dumps(self.downloads)
        dd = json.loads(ddump)
        dheaders = ['url', 'option', 'filename']
        self.downloadmodel = DownloadModel(dd, dheaders)
        self.downloadQueueView.setModel(self.downloadmodel)
        self.downloadView.setModel(self.downloadmodel)
        self.downloadmodel.layoutChanged.emit()

    def selectcapture(self):
        indexes = self.captureQueueView.selectionModel().selectedRows()
        for index in sorted(indexes):
            # Remove the item and refresh.
            dselect = index.row()
            with open("captures.json", "r") as f:
                links = json.load(f)
            s = links[dselect]
            u = s['url']
            q = s['quality']
            o = s['option']
            f = s['filename']
            if q == 'Highest':
                self.downloadQuality.setCurrentIndex(3)
            elif q == 'Lowest':
                self.downloadQuality.setCurrentIndex(2)
            elif q == 'Playlist':
                self.downloadQuality.setCurrentIndex(1)
            else:
                self.downloadQuality.setCurrentIndex(0)
            self.captureText2.setText(u)
            if f:
                self.captureparseOutput.setCheckState(Qt.Checked)
                if o == "MUX":
                    self.captureMuxOutput.click()
                else:
                    self.capturerenameOutput.click()
                self.captureparseName.setText(f)

    def selectdownload(self):
        indexes = self.downloadQueueView.selectionModel().selectedRows()
        for index in sorted(indexes):
            # Remove the item and refresh.
            dselect = index.row()
            with open("downloads.json", "r") as f:
                links = json.load(f)
            s = links[dselect]
            u = s['url']
            o = s['option']
            f = s['filename']
            self.downloadText2.setText(u)
            if f:
                self.downloadparseOutput.setCheckState(Qt.Checked)
                if o == "MUX":
                    self.downloadMuxOutput.click()
                else:
                    self.downloadrenameOutput.click()
                self.downloadparseName.setText(f)

    def ADstate(self, s):
        if (s == Qt.Checked):
            self.downloadQuality.setEnabled(True)
            self.captureparseOutput.setEnabled(True)
        else:
            self.downloadQuality.setEnabled(False)
            self.captureparseOutput.setEnabled(False)

    def captureParsestate(self, s):
        if (s == Qt.Checked):
            self.captureparseName.setEnabled(True)
            self.captureMuxOutput.setEnabled(True)
            self.capturerenameOutput.setEnabled(True)
        else:
            self.captureparseName.setEnabled(False)
            self.captureMuxOutput.setEnabled(False)
            self.capturerenameOutput.setEnabled(False)

    def downloadParsestate(self, s):
        if (s == Qt.Checked):
            self.downloadparseName.setEnabled(True)
            self.downloadMuxOutput.setEnabled(True)
            self.downloadrenameOutput.setEnabled(True)
        else:
            self.downloadparseName.setEnabled(False)
            self.downloadMuxOutput.setEnabled(False)
            self.downloadrenameOutput.setEnabled(False)

    def rename_file(self):
        with open("download_temp.json", "r") as f:
            dt = json.load(f)
            rn = dt['rename']
            dfn = dt['filename']
        if rn:
            fn = dt['fn']
            with open("preferences.json", "r") as f:
                pref = json.load(f)
            da = pref['da']
            if da:
                df = pref['df']
                if df:
                    os.rename(df+"/"+dfn, df+"/"+fn)
                    self.message("Renaming " + dfn + " to " + fn)
                else:
                    os.rename(dfn, fn)
                    self.message("Renaming " + dfn + " to " + fn)

    def merge_two_dicts(self, x, y):
        """Given two dictionaries, merge them into a new dict as a shallow copy."""
        z = x.copy()
        z.update(y)
        return z

    def message(self, s):
        self.statustext.appendPlainText(s)

    def handle_stderr(self):
        errdata = self.p.readAllStandardError()
        errbytes = QByteArray(errdata)
        stderr = errbytes.data().decode()
        dfilename = download_filename(stderr)
        if dfilename:
            with open("download_temp.json", "r") as f:
                df = json.load(f)
                dn = dict(filename=dfilename)
                nd =self.merge_two_dicts(df, dn)
            with open("download_temp.json", "w") as f:
                fn = json.dump(nd, f)
        progress = simple_percent_parser(stderr)
        if progress:
            self.progressBar1.setValue(progress)
            self.progressBar2.setValue(progress)
            self.progressBar3.setValue(progress)
            self.progressBar4.setValue(progress)
        self.message(stderr)

    def handle_stdout(self):
        if 'last' in dir():
            x = True
        else:
            last = ''
        outdata = self.p.readAllStandardOutput()
        outbytes = QByteArray(outdata)
        strstdout = outbytes.data().decode()
        stdout = strstdout.rstrip()
        downloadlinks = video_link_locator(stdout)
        init = capture_init(stdout)
        if init:
            self.t = QTimer()
            self.t.setInterval(5000)
            self.t.timeout.connect(self.timeout)
            if not self.t.isActive():
                self.t.start()
        if downloadlinks:
            link = downloadlinks.replace("Detected ", "")
            if last != link:
                self.links.append(dict(link=link))
            with open("out_temp.json", "w") as f:
                linkf = json.dump(self.links, f)
            last = link
            self.t.stop()
            if not self.t.isActive():
                self.t.start(2500)
        self.message(stdout)

    def timeout(self):
        if self.p:
            self.p.kill()
        self.t.stop()
        with open("capture_temp.json", "r") as f:
            co = json.load(f)
        auto = co['auto']
        if auto:
            dq = co['quality']
            if dq == "Select":
                dlg = QualitySelectDialog()
                dlg.open()
            else:
                sq = self.findquality(dq)
                self.add2DownloadQueue(sq)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def process_finished(self):
        self.message("Process finished.")
        self.p = None
        mode = QProcessEnvironment.value(self.env, "Mode")
        if mode == "download":
            self.rename_file()
        self.StartButton.setEnabled(True),
        self.CaptureStartButton.setEnabled(True)
        self.DownloadStartButton.setEnabled(True)
        self.CaptureCancelButton.setEnabled(False)
        self.DownloadCancelButton.setEnabled(False)
        self.progressBar1.setVisible(False)
        self.progressBar2.setVisible(False)
        self.progressBar3.setVisible(False)
        self.progressBar4.setVisible(False)

    def start_capture(self, URL):
        if self.p is None:  # No process running.
            self.message("Starting Capture")
            self.links = []
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.env = QProcessEnvironment.systemEnvironment()
            self.env.insert("KDAM_NCOLS", "0")
            self.env.insert("Mode", "capture")
            self.p.setProcessEnvironment(self.env)
            self.p.start("vsd capture --color never " + URL)
            self.StartButton.setEnabled(False),
            self.CaptureStartButton.setEnabled(False)
            self.DownloadStartButton.setEnabled(False)
            self.CaptureCancelButton.setEnabled(True)

    def start_download(self, URL):
        if self.p is None:  # No process running.
            self.message("Starting Download")
            flags = self.buildflags()
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.env = QProcessEnvironment.systemEnvironment()
            self.env.insert("KDAM_NCOLS", "0") # Remove Progress bar
            self.env.insert("Mode", "download")
            self.p.setProcessEnvironment(self.env)
            self.p.start("vsd save --color never " + flags + " " + URL)
            self.StartButton.setEnabled(False),
            self.CaptureStartButton.setEnabled(False)
            self.DownloadStartButton.setEnabled(False)
            self.DownloadCancelButton.setEnabled(True)
            self.progressBar1.setVisible(True)
            self.progressBar2.setVisible(True)
            self.progressBar3.setVisible(True)
            self.progressBar4.setVisible(True)

    def CaptureNow(self):
        k = strftime("%Y%m%d%H%M%S", gmtime())
        u = self.captureText2.text()
        a = self.autoDownload.isChecked()
        Q = self.downloadQuality.currentIndex()
        O1 = self.captureMuxOutput.isChecked()
        O2 = self.capturerenameOutput.isChecked()
        if O1:
            o = 'MUX'
        elif O2:
            o = 'Rename'
        else:
            o = False
        f = self.captureparseName.text()
        if Q == 3:
            q = "Highest"
        elif Q == 2:
            q = "Lowest"
        elif Q == 1:
            q = "Playlist"
        else:
            q = "Select"
        c = dict(cid=k, url=u, auto=a, quality=q, option=o, filename=f)

        with open("capture_temp.json", "w") as f:
            linkf = json.dump(c, f)
        self.start_capture(u)
        self.removecompletecaptures(u)

    def removecompletecaptures(self, u):
        with open("captures.json", "r") as f:
            captures = json.load(f)
        for x in captures:
            if u in captures:
                index = captures.key()
                self.message('Current capture found in queue.')
                self.capturemodel.removeRow(index)
                self.message('Removing captured item from queue.')

    def findquality(self, dq):
        playlist = False
        pl = ""
        highest = ""
        lowest = ""
        with open("out_temp.json", "r") as f:
            dwnld = json.load(f)
        pl_re = re.compile('\A\w/playlist.m3u8')
        for x in dwnld:
            link = x['link']
            pl = pl_re.search(link)
            if pl:
                playlist = True
        if playlist:
            dwnld_count = len(dwnld)
            if dwnld_count == 2:
                highest = dwnld[1]['link']
                lowest = dwnld[1]['link']
            if dwnld_count == 3:
                highest = dwnld[2]['link']
                lowest = dwnld[1]['link']
        else:
            dwnld_count = len(dwnld)
            if dwnld_count == 2:
                highest = dwnld[1]['link']
                lowest = dwnld[0]['link']
            if dwnld_count == 3:
                highest = dwnld[2]['link']
                lowest = dwnld[0]['link']
        if dq == "Playlist":
            if pl:
                self.message("Adding to downloads: " + pl)
                return pl
            else:
                self.message('search failed to find a suitable match.')
                return "Failure"

        if dq == "Highest":
            if highest:
                self.message("Adding to downloads: " + highest)
                return highest
            else:
                self.message('search failed to find a suitable match.')
                return "Failure"

        if dq == "Lowest":
            if lowest:
                self.message("Adding to downloads: " + lowest)
                return lowest
            else:
                self.message('search failed to find a suitable match.')
                return "Failure"

    def DownloadNow(self):
        rn = self.downloadrenameOutput.isChecked()
        u = self.downloadText2.text()
        fn = self.downloadparseName.text()
        if rn:
            rename = dict(rename="True", fn=fn)
        else:
            rename = dict(rename="False", fn="none")
        if rename:
            with open("download_temp.json", "w") as f:
                renamef = json.dump(rename, f)
        self.start_download(u)

    def addDownload(self):
        key = strftime("%Y%m%d%H%M%S", gmtime())
        http = self.downloadText2.text()
        O1 = self.downloadMuxOutput.isChecked()
        O2 = self.downloadrenameOutput.isChecked()
        if O1:
            O = 'MUX'
        elif O2:
            O = 'Rename'
        else:
            O = False
        File = self.downloadparseName.text()
        FileName = str(File)
        self.downloadmodel.appendRow(key, http, O, FileName)
        self.downloadmodel.layoutChanged.emit()
        self.downloadText2.setText("")
        self.downloadparseName.setText("")

    def addcapture(self):
        key = strftime("%Y%m%d%H%M%S", gmtime())
        http = self.captureText2.text()
        Q = self.downloadQuality.currentIndex()
        O1 = self.captureMuxOutput.isChecked()
        O2 = self.capturerenameOutput.isChecked()
        if O1:
            O = 'MUX'
        elif O2:
            O = 'Rename'
        else:
            O = False
        File = self.captureparseName.text()
        FileName = str(File)
        if Q == 3:
            Quality = "Highest"
        elif Q == 2:
            Quality = "Lowest"
        elif Q == 1:
            Quality = "Playlist"
        else:
            Quality = "Select"
        self.capturemodel.appendRow(key, http, Quality, O, FileName)
        self.capturemodel.layoutChanged.emit()
        self.captureText2.setText("")
        self.captureparseName.setText("")

    def deletecapture(self):
        indexes = self.captureQueueView.selectionModel().selectedRows()
        for index in sorted(indexes):
            # Remove the item and refresh.
            self.capturemodel.removeRow(index.row())
        self.capturemodel.layoutChanged.emit()
        # Clear the selection (as it is no longer valid).
        self.captureQueueView.clearSelection()

    def add2DownloadQueue(self, u):
        with open("capture_temp.json", "r") as f:
            captures = json.load(f)
        cdump = json.dumps(captures)
        cd = json.loads(cdump)
        k = cd['cid']
        o = cd['option']
        f = cd['filename']
        if f == '':
            o = "None"
            f = "None"
        self.downloadmodel.appendRow(k, u, o, f)
        self.downloadrefresh()

    def deletedownload(self):
        indexes = self.downloadQueueView.selectionModel().selectedRows()
        for index in sorted(indexes):
            # Remove the item and refresh.
            self.downloadmodel.removeRow(index.row())
        self.downloadmodel.layoutChanged.emit()
        # Clear the selection (as it is no longer valid).
        self.downloadQueueView.clearSelection()

    def loadCaptures(self):
        try:
            with open("captures.json", "r") as f:
                self.captures = json.load(f)
        except Exception:
            self.captures = []
            pass

    def loadDownloads(self):
        try:
            with open("downloads.json", "r") as f:
                self.downloads = json.load(f)
        except Exception:
            self.downloads = []
            pass

    def refresh_downloads(d):
        self = MainWindow()
        self.downloadmodel.layoutAboutToBeChanged.emit()
        self.downloads = d
        self.downloadmodel.layoutChanged.emit()

    def start_download_from_select(u):
        self = MainWindow()
        self.start_download(u)

    def loadPreferences(self):
        dlg = PreferencesDialog()
        dlg.exec_()

    def buildflags(self):
        flags = "--skip-prompts"
        prefs_exists = exists('preferences.json')
        if prefs_exists:
            with open("preferences.json", "r") as f:
                prefs = json.load(f)
            with open("RFC5646.json", "r") as f:
                rfc = json.load(f)
                lang = rfc['RFC5646_LANGUAGE_TAGS']
            with open("agents.json", "r") as f:
                agents = json.load(f)
                agent = agents['agents']
            da = prefs['da']
            if da == 'True':
                df = prefs['df']
                if df:
                    flags = flags + " --directory " + df
            ra = prefs['ra']
            if ra == 'True':
                rt = prefs['rt']
                if rt:
                    flags = flags + " --retry-count " + rt
            ta = prefs['ta']
            if ta == 'True':
                tt = prefs['tt']
                if tt:
                    flags = flags + " --threads " + tt
            la = prefs['la']
            if la == 'True':
                ls = prefs['ls']
                if ls:
                    lslang = lang[ls]
                    flags = flags + " --prefer-audio-lang " + lslang
            sa = prefs['sa']
            if sa == 'True':
                ss = prefs['ss']
                if ss:
                    sslang = lang[ss]
                    flags = flags + " --prefer-subs-lang " + sslang
            aqa = prefs['aqa']
            if aqa == 'True':
                aq = prefs['aq']
                if aq:
                    flags = flags + " --quality " + aq
            certa = prefs['certa']
            if certa == 'True':
                flags = flags + " --no-certificate-checks"
            ca = prefs['ca']
            if ca == 'True':
                ct = prefs['ct']
                if ct:
                    flags = flags + " --cookies " + ct
            pra = prefs['pra']
            if pra:
                prt = prefs['prt']
                if prt:
                    flags = flags + " --proxy " + prt
            ha = prefs['ha']
            if ha == 'True':
                hv = prefs['hv']
                if hv:
                    for x in hv:
                        flags = flags + " --header " + x
            dca = prefs['dca']
            if dca == 'True':
                dv = prefs['dv']
                if dv:
                    for x in dv:
                        flags = flags + " --set-cookie " + x
            aga = prefs['aga']
            if aga == 'True':
                ags = prefs['ags']
                if ags:
                    ag = agent[ags]
                    flags = flags + " --user-agent " + ag
            aka = prefs['aka']
            if aka == 'True':
                flags = flags + " --all-keys"
            cka = prefs['cka']
            if cka:
                ckv = prefs['ckv']
                if ckv:
                    for x in ckv:
                        flags = flags + " --key " + x
            nda = prefs['nda']
            if nda == 'True':
                flags = flags + " --no-decrypt"
            return flags


class QualitySelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.loadDownloads()
        cd = self.downloads
        cheaders = ['url', 'option', 'filename']
        self.downloadmodel = DownloadModel(cd, cheaders)

        with open("out_temp.json", "r") as f:
            links = json.load(f)
        cdump = json.dumps(links)
        cd = json.loads(cdump)
        cheaders = ['link']
        self.qselectmodel = QSelectModel(cd, cheaders)
        self.setWindowTitle("File Selection")
        self.resize(QSize(600, 300))
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        message = QLabel("Select File you want to download:")
        self.layout.addWidget(message)
        self.captureView = QTableView()
        self.captureView.setShowGrid(False)
        self.layout.addWidget(self.captureView)
        self.captureView.setModel(self.qselectmodel)
        self.captureView.setColumnWidth(0, 450)
        self.captureView.setColumnWidth(3, 150)
        self.captureView.resizeColumnsToContents()
        selectButton = QPushButton("Select")
        self.layout.addWidget(selectButton)
        selectButton.clicked.connect(lambda: self.select())

    def loadDownloads(self):
        try:
            with open("downloads.json", "r") as f:
                self.downloads = json.load(f)
        except Exception:
            self.downloads = []
            pass

    def select(self):
        indexes = self.captureView.selectionModel().selectedRows()
        index = indexes[0]
        uselect = index.row()
        with open("out_temp.json", "r") as f:
            links = json.load(f)
        uitem = links[uselect]
        u = uitem['link']
        with open("capture_temp.json", "r") as f:
            captures = json.load(f)
        cdump = json.dumps(captures)
        cd = json.loads(cdump)
        a = cd['auto']
        if a:
            self.DownloadFromQueue(u)
        else:
            self.add2Queue(u)

    def add2Queue(self, u):
        with open("capture_temp.json", "r") as f:
            captures = json.load(f)
        cdump = json.dumps(captures)
        cd = json.loads(cdump)
        k = cd['cid']
        o = cd['option']
        f = cd['filename']
        if f == '':
            o = "None"
            f = "None"
        self.downloadmodel.appendRow(k, u, o, f)
        MainWindow.refresh_downloads(self.downloads)
        self.close()

    def DownloadFromQueue(self, u):
        k = strftime("%Y%m%d%H%M%S", gmtime())
        with open("capture_temp.json", "r") as f:
            captures = json.load(f)
        cdump = json.dumps(captures)
        cd = json.loads(cdump)
        o = cd['option']
        f = cd['filename']
        c = dict(cid=k, url=u, option=o, filename=f)
        with open("download_temp.json", "w") as f:
            linkf = json.dump(c, f)
        #MainWindow.start_download_from_select(u)
        self.add2Queue(u)
        #self.close()

class PreferencesDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Preferences")

        tagFont = QtGui.QFont()
        tagFont.setBold(True)
        self.scroll = QScrollArea()
        self.resize(QSize(600, 300))
        self.scrollLayout = QVBoxLayout()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.main = QVBoxLayout()
        self.w = QWidget()
        self.main.addWidget(self.w)
        #self.w.setLayout(self.layout)
        #generalLabel = QLabel("General Options")
        #self.layout.addWidget(generalLabel)
        #generalLabel.setFont(tagFont)

        general_container = Container("General Options")
        self.layout.addWidget(general_container)
        self.glayout = QVBoxLayout(general_container.contentWidget)
        self.glayout1 = QHBoxLayout(general_container.contentWidget)
        self.glayout2 = QGridLayout(general_container.contentWidget)

        generalbox1 = QWidget()
        self.glayout.addWidget(generalbox1)
        generalbox1.setLayout(self.glayout1)
        self.directoryActive = QCheckBox("Use directory path for temporarily downloaded files:")
        self.glayout1.addWidget(self.directoryActive)
        self.directoryFolder = QLineEdit()
        self.glayout1.addWidget(self.directoryFolder)
        self.directoryFolder.setWhatsThis("Directory to save all downloaded content.")
        self.folderButton = QPushButton("Select")
        self.glayout1.addWidget(self.folderButton)
        self.folderButton.clicked.connect(lambda: self.directory_select())

        generalbox2 = QWidget()
        self.glayout.addWidget(generalbox2)
        generalbox2.setLayout(self.glayout2)
        self.retriesActive = QCheckBox("Adjust the maximum number of retries to download an individual segment [default: 15]:")
        self.glayout2.addWidget(self.retriesActive, 0, 0)
        self.retriesText = QLineEdit()
        self.glayout2.addWidget(self.retriesText, 0, 1)
        self.threadsActive = QCheckBox(
            "Adjust the maximum number of threads for parallel downloading of segments. (range 1-16 inclusive) [default: 5]:")
        self.glayout2.addWidget(self.threadsActive,1 , 0)
        self.threadsText = QLineEdit()
        self.glayout2.addWidget(self.threadsText, 1, 1)
        self.glayout2.setAlignment(Qt.AlignTop)
        generalbox1.setContentsMargins(0, 0, 0, 0)
        generalbox2.setContentsMargins(0, 0, 0, 0)

        #playlistLabel = QLabel("Playlist Options")
        #self.layout.addWidget(playlistLabel)
        #playlistLabel.setFont(tagFont)

        playlist_container = Container("Playlist Options")
        self.layout.addWidget(playlist_container)
        self.playout = QVBoxLayout(playlist_container.contentWidget)
        self.playout1 = QGridLayout(playlist_container.contentWidget)

        playlistbox1 = QWidget()
        self.playout.addWidget(playlistbox1)
        playlistbox1.setLayout(self.playout1)
        self.languageActive = QCheckBox("Use Preferred language for audio streams:")
        self.playout1.addWidget(self.languageActive, 0, 0)
        self.languageSelect = QComboBox()
        self.playout1.addWidget(self.languageSelect, 0, 1)
        self.subtitlesActive = QCheckBox(
            "Use Preferred language for subtitles streams:")
        self.playout1.addWidget(self.subtitlesActive, 0, 2)
        self.subtitlesSelect = QComboBox()
        self.playout1.addWidget(self.subtitlesSelect, 0, 3)
        self.aqActive = QCheckBox(
            "Use automatic selection of resolution from playlist:")
        self.playout1.addWidget(self.aqActive, 1, 0)
        self.aqSelect = QComboBox()
        self.playout1.addWidget(self.aqSelect, 1, 1)
        self.aqSelect.addItems(["lowest", "min", "144p", "240p", "360p", "480p", "720p", "hd", "1080p", "fhd", "2k", "1440p", "qhd", "4k", "8k", "highest", "max"])
        self.playout1.setAlignment(Qt.AlignTop)
        playlistbox1.setContentsMargins(0, 0, 0, 0)

        #clientLabel = QLabel("Client Options")
        #self.layout.addWidget(clientLabel)
        #clientLabel.setFont(tagFont)

        client_container = Container("Client Options")
        self.layout.addWidget(client_container)
        self.clayout = QVBoxLayout(client_container.contentWidget)
        self.clayout1 = QGridLayout(client_container.contentWidget)
        self.clayout2 = QVBoxLayout(client_container.contentWidget)
        self.clayout3 = QVBoxLayout(client_container.contentWidget)

        clientbox1 = QWidget()
        self.clayout.addWidget(clientbox1)
        clientbox1.setLayout(self.clayout1)
        self.certificatesActive = QCheckBox(
            "Skip checking and validation of site certificates.")
        self.clayout1.addWidget(self.certificatesActive, 0, 0)
        self.cookiesActive = QCheckBox(
            "Use cookies values to fill request client:")
        self.clayout1.addWidget(self.cookiesActive, 1, 0)
        self.cookiesText = QLineEdit()
        self.clayout1.addWidget(self.cookiesText, 1, 1)
        self.proxiesActive = QCheckBox(
            "Use http(s) / socks proxy address for requests:")
        self.clayout1.addWidget(self.proxiesActive, 2, 0)
        self.proxiesText = QLineEdit()
        self.clayout1.addWidget(self.proxiesText, 2, 1)
        self.headersActive = QCheckBox(
            "Use custom headers for requests (In <KEY> <VALUE> format):")
        self.clayout1.addWidget(self.headersActive, 0, 2)
        self.headersText = QLineEdit()
        self.clayout1.addWidget(self.headersText, 0, 3)
        self.addHeaderButton = QPushButton("Add")
        self.addHeaderButton.clicked.connect(lambda: self.addHeader())
        self.clayout1.addWidget(self.addHeaderButton, 0, 4)
        self.headersView = QListWidget()
        self.headersView.itemDoubleClicked.connect(lambda: self.selectHeader())
        self.headersView.setFixedSize(500, 75)
        self.clayout1.addWidget(self.headersView, 1, 2)
        headerbtnbox = QWidget()
        self.clayout1.addWidget(headerbtnbox, 1, 3)
        headerbtnbox.setLayout(self.clayout2)
        self.removeHeaderButton = QPushButton("Remove")
        self.clayout2.addWidget(self.removeHeaderButton)
        self.removeHeaderButton.clicked.connect(lambda: self.removeHeader())
        self.clearHeaderButton = QPushButton("Clear")
        self.clayout2.addWidget(self.clearHeaderButton)
        self.clearHeaderButton.clicked.connect(lambda: self.clearHeader())
        self.clayout2.setAlignment(Qt.AlignTop)
        self.domainActive = QCheckBox(
            "Use custom cookies per domain (in <SET_COOKIE> <URL> format):")
        self.clayout1.addWidget(self.domainActive, 2, 2)
        self.domainText = QLineEdit()
        self.clayout1.addWidget(self.domainText, 2, 3)
        self.addDomainButton = QPushButton("Add")
        self.addDomainButton.clicked.connect(lambda: self.addDomain())
        self.clayout1.addWidget(self.addDomainButton, 2, 4)
        self.domainView = QListWidget()
        self.domainView.itemDoubleClicked.connect(lambda: self.selectDomain())
        self.domainView.setFixedSize(500, 75)
        self.clayout1.addWidget(self.domainView, 3, 2)
        domainbtnbox = QWidget()
        self.clayout1.addWidget(domainbtnbox, 3, 3)
        domainbtnbox.setLayout(self.clayout3)
        self.removeDomainButton = QPushButton("Remove")
        self.clayout3.addWidget(self.removeDomainButton)
        self.removeDomainButton.clicked.connect(lambda: self.removeDomain())
        self.clearDomainButton = QPushButton("Clear")
        self.clayout3.addWidget(self.clearDomainButton)
        self.clearDomainButton.clicked.connect(lambda: self.clearDomain())
        self.clayout3.setAlignment(Qt.AlignTop)
        self.agentActive = QCheckBox(
            "Use custom agent header for requests:")
        self.clayout1.addWidget(self.agentActive, 3, 0)
        self.agentSelect = QComboBox()
        self.clayout1.addWidget(self.agentSelect, 3, 1)
        self.clayout.setAlignment(Qt.AlignTop)
        self.clayout1.setAlignment(Qt.AlignTop)
        clientbox1.setContentsMargins(0, 0, 0, 0)

        decrypt_container = Container("Decrypt Options")
        self.layout.addWidget(decrypt_container)
        self.dlayout = QVBoxLayout(decrypt_container.contentWidget)
        self.dlayout1 = QGridLayout(decrypt_container.contentWidget)
        self.ckeylayout = QGridLayout(decrypt_container.contentWidget)
        self.dlayout2 = QVBoxLayout(decrypt_container.contentWidget)

        decryptbox1 = QWidget()
        self.dlayout.addWidget(decryptbox1)
        decryptbox1.setLayout(self.dlayout1)
        self.nodecryptActive = QCheckBox(
            "Download encrypted streams without decrypting them. Note that 'Send to ffmpeg' is ignored.")
        self.dlayout.addWidget(self.nodecryptActive)
        self.allkeysActive = QCheckBox(
            "Use all supplied keys for decryption.")
        self.dlayout1.addWidget(self.allkeysActive, 0, 0)
        ckeybox = QWidget()
        self.dlayout1.addWidget(ckeybox, 0, 1)
        ckeybox.setLayout(self.ckeylayout)
        self.ckeysActive = QCheckBox(
            "Use custom keys for decrypting encrypted streams.:")
        self.ckeylayout.addWidget(self.ckeysActive, 0, 0)
        self.ckeysText = QLineEdit()
        self.ckeylayout.addWidget(self.ckeysText, 0, 1)
        self.addCkeyButton = QPushButton("Add")
        self.addCkeyButton.clicked.connect(lambda: self.addCkey())
        self.ckeylayout.addWidget(self.addCkeyButton, 0, 2)
        self.ckeyView = QListWidget()
        self.ckeyView.itemDoubleClicked.connect(lambda: self.selectCkey())
        self.ckeyView.setFixedSize(500, 75)
        self.ckeylayout.addWidget(self.ckeyView, 1, 0)
        ckeybtnbox = QWidget()
        self.ckeylayout.addWidget(ckeybtnbox, 1, 1)
        ckeybtnbox.setLayout(self.dlayout2)
        self.removeDomainButton = QPushButton("Remove")
        self.dlayout2.addWidget(self.removeDomainButton)
        self.removeDomainButton.clicked.connect(lambda: self.removeCkey())
        self.clearDomainButton = QPushButton("Clear")
        self.dlayout2.addWidget(self.clearDomainButton)
        self.clearDomainButton.clicked.connect(lambda: self.clearCkey())
        ckeybox.setFixedSize(700, 125)
        self.dlayout2.setAlignment(Qt.AlignTop)
        self.dlayout.setAlignment(Qt.AlignTop)
        self.dlayout1.setAlignment(Qt.AlignTop)
        decryptbox1.setContentsMargins(0, 0, 0, 0)

        self.saveButton = QPushButton("Save")
        self.layout.addWidget(self.saveButton)
        self.saveButton.clicked.connect(lambda: self.savePreferences())
        self.loaddata()
        self.loadpreferences()


        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.w)

        self.layout.setAlignment(Qt.AlignTop)

    def loaddata(self):
        with open("RFC5646.json", "r") as f:
            RFC = json.load(f)
            languages = RFC['RFC5646_LANGUAGE_TAGS']
        for x in languages:
            self.languageSelect.addItem(x)
            self.subtitlesSelect.addItem(x)
        with open("agents.json", "r") as f:
            agent = json.load(f)
            agents = agent['agents']
        for x in agents:
            self.agentSelect.addItem(x)

    def loadpreferences(self):
        prefs_exists = exists('preferences.json')
        if prefs_exists:
            with open("preferences.json", "r") as f:
                prefs = json.load(f)
            da = prefs['da']
            if da == 'True':
                self.directoryActive.setCheckState(Qt.Checked)
            df = prefs['df']
            if df:
                self.directoryFolder.setText(df)
            ra = prefs['ra']
            if ra == 'True':
                self.retriesActive.setCheckState(Qt.Checked)
            rt = prefs['rt']
            if rt:
                self.retriesText.setText(rt)
            ta = prefs['ta']
            if ta == 'True':
                self.threadsActive.setCheckState(Qt.Checked)
            tt = prefs['tt']
            if tt:
                self.threadsText.setText(tt)
            la = prefs['la']
            if la == 'True':
                self.languageActive.setCheckState(Qt.Checked)
            ls = prefs['ls']
            if ls:
                index = self.languageSelect.findText(ls, Qt.MatchFixedString)
                if index >= 0:
                    self.languageSelect.setCurrentIndex(index)
            sa = prefs['sa']
            if sa == 'True':
                self.subtitlesActive.setCheckState(Qt.Checked)
            ss = prefs['ss']
            if ss:
                index = self.subtitlesSelect.findText(ss, Qt.MatchFixedString)
                if index >= 0:
                    self.subtitlesSelect.setCurrentIndex(index)
            aqa = prefs['aqa']
            if aqa == 'True':
                self.aqActive.setCheckState(Qt.Checked)
            aq = prefs['aq']
            if aq:
                index = self.aqSelect.findText(aq, Qt.MatchFixedString)
                if index >= 0:
                    self.aqSelect.setCurrentIndex(index)
            certa = prefs['certa']
            if certa == 'True':
                self.certificatesActive.setCheckState(Qt.Checked)
            ca = prefs['ca']
            if ca == 'True':
                self.cookiesActive.setCheckState(Qt.Checked)
            ct = prefs['ct']
            if ct:
                self.cookiesText.setText(ct)
            pra = prefs['pra']
            if pra == 'True':
                self.proxiesActive.setCheckState(Qt.Checked)
            prt = prefs['prt']
            if prt:
                self.proxiesText.setText(prt)
            ha = prefs['ha']
            if ha == 'True':
                self.headersActive.setCheckState(Qt.Checked)
            hv = prefs['hv']
            for x in hv:
                self.headersView.addItem(x)
            dca = prefs['dca']
            if dca == 'True':
                self.cookiesActive.setCheckState(Qt.Checked)
            dv = prefs['dv']
            for x in dv:
                self.domainView.addItem(x)
            aga = prefs['aga']
            if aga == 'True':
                self.agentActive.setCheckState(Qt.Checked)
            ags = prefs['ags']
            if ags:
                index = self.agentSelect.findText(ags, Qt.MatchFixedString)
                if index >= 0:
                    self.agentSelect.setCurrentIndex(index)
            aka = prefs['aka']
            if aka == 'True':
                self.allkeysActive.setCheckState(Qt.Checked)
            cka = prefs['cka']
            if cka == 'True':
                self.ckeysActive.setCheckState(Qt.Checked)
            ckv = prefs['ckv']
            for x in ckv:
                self.ckeyView.addItem(x)
            nda = prefs['nda']
            if nda == 'True':
                 self.nodecryptActive.setCheckState(Qt.Checked)


    def directory_select(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directoryFolder.setText(file)

    def addHeader(self):
        header = self.headersText.text()
        self.headersView.addItem(header)
        self.headersText.setText("")

    def removeHeader(self):
        selected = self.headersView.currentRow()
        if selected:
            self.headersView.takeItem(selected)

    def clearHeader(self):
        self.headersView.clear()

    def selectHeader(self):
        selected = self.headersView.currentItem()
        self.headersText.setText(str(selected))

    def addDomain(self):
        domain = self.domainText.text()
        self.domainView.addItem(domain)
        self.domainText.setText("")

    def removeDomain(self):
        selected = self.domainView.currentRow()
        if selected:
            self.domainView.takeItem(selected)

    def clearDomain(self):
        self.domainView.clear()

    def selectDomain(self):
        selected = self.domainView.currentItem()
        self.domainText.setText(str(selected))

    def addCkey(self):
        ckey = self.ckeysText.text()
        self.ckeyView.addItem(ckey)
        self.ckeysText.setText("")

    def removeCkey(self):
        selected = self.ckeyView.currentRow()
        if selected:
            self.ckeyView.takeItem(selected)

    def clearCkey(self):
        self.ckeyView.clear()

    def selectcKey(self):
        selected = self.ckeyView.currentItem()
        self.ckeysText.setText(str(selected))

    def savePreferences(self):
        h_items = []
        d_items = []
        ck_items = []
        hv = ''
        ckv = ''
        dv = ''
        da = self.directoryActive.checkState()
        if da:
            da = 'True'
        else:
            da = 'False'
        df = self.directoryFolder.text()
        ra = self.retriesActive.checkState()
        if ra:
            ra = 'True'
        else:
            ra = 'False'
        rt = self.retriesText.text()
        ta = self.threadsActive.checkState()
        if ta:
            ta = 'True'
        else:
            ta = 'False'
        tt = self.threadsText.text()
        la = self.languageActive.checkState()
        if la:
            la = 'True'
        else:
            la = 'False'
        ls = self.languageSelect.currentText()
        sa = self.subtitlesActive.checkState()
        if sa:
            sa = 'True'
        else:
            sa = 'False'
        ss = self.subtitlesSelect.currentText()
        aqa = self.aqActive.checkState()
        if aqa:
            aqa = 'True'
        else:
            aqa = 'False'
        aq = self.aqSelect.currentText()
        certa = self.certificatesActive.checkState()
        if certa:
            certa = 'True'
        else:
            certa = 'False'
        ca = self.cookiesActive.checkState()
        if ca:
            ca = 'True'
        else:
            ca = 'False'
        pra = self.proxiesActive.checkState()
        if pra:
            pra = 'True'
        else:
            pra = 'False'
        prt = self.proxiesText.text()
        ct = self.cookiesText.text()
        ha = self.headersActive.checkState()
        if ha:
            ha = 'True'
        else:
            ha = 'False'
        for x in range(self.headersView.count()):
            h_item = self.headersView.item(x).text()
            h_items.append(str(h_item))
            hv = h_items
        dca = self.domainActive.checkState()
        if dca:
            dca = 'True'
        else:
            dca = 'False'
        for x in range(self.domainView.count()):
            d_item = self.domainView.item(x).text()
            d_items.append(str(d_item))
            dv = d_items
        aga = self.agentActive.checkState()
        if aga:
            aga = 'True'
        else:
            aga = 'False'
        ags = self.agentSelect.currentText()
        aka = self.allkeysActive.checkState()
        if aka:
            aka = 'True'
        else:
            aka = 'False'
        cka = self.ckeysActive.checkState()
        if cka:
            cka = 'True'
        else:
            cka = 'False'
        for x in range(self.ckeyView.count()):
            ck_item = self.ckeyView.item(x).text()
            ck_items.append(str(ck_item))
            ckv = ck_items
        nda = self.nodecryptActive.checkState()
        if nda:
            nda = 'True'
        else:
            nda = 'False'

        data = dict(da=da, df=df, ra=ra, rt=rt, ta=ta, tt=tt, la=la, ls=ls, sa=sa, ss=ss, aqa=aqa, aq=aq, certa=certa, ca=ca, pra=pra, prt=prt, ct=ct, ha=ha, hv=hv, dca=dca, dv=dv, aga=aga, ags=ags, aka=aka, cka=cka, ckv=ckv, nda=nda)

        with open("preferences.json", "w") as f:
            linkf = json.dump(data, f)

class Header(QWidget):
    """Header class for collapsible group"""

    def __init__(self, name, content_widget):
        """Header Class Constructor to initialize the object.

        Args:
            name (str): Name for the header
            content_widget (QtWidgets.QWidget): Widget containing child elements
        """
        super(Header, self).__init__()
        self.content = content_widget
        self.expand_ico = QtGui.QPixmap(":teDownArrow.png")
        self.collapse_ico = QtGui.QPixmap(":teRightArrow.png")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        stacked = QStackedLayout(self)
        stacked.setStackingMode(QStackedLayout.StackAll)
        background = QLabel()
        background.setStyleSheet("QLabel{ background-color: rgb(93, 93, 93); border-radius:2px}")

        widget = QWidget()
        layout = QHBoxLayout(widget)

        self.icon = QLabel()
        self.icon.setPixmap(self.expand_ico)
        layout.addWidget(self.icon)
        layout.setContentsMargins(11, 0, 11, 0)

        font = QtGui.QFont()
        font.setBold(True)
        label = QLabel(name)
        label.setFont(font)

        layout.addWidget(label)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        stacked.addWidget(widget)
        stacked.addWidget(background)
        background.setMinimumHeight(layout.sizeHint().height() * 1.5)

    def mousePressEvent(self, *args):
        """Handle mouse events, call the function to toggle groups"""
        self.expand() if not self.content.isVisible() else self.collapse()

    def expand(self):
        self.content.setVisible(True)
        self.icon.setPixmap(self.expand_ico)

    def collapse(self):
        self.content.setVisible(False)
        self.icon.setPixmap(self.collapse_ico)

class Container(QWidget):
    """Class for creating a collapsible group similar to how it is implement in Maya

        Examples:
            Simple example of how to add a Container to a QVBoxLayout and attach a QGridLayout

            >>> layout = QVBoxLayout()
            >>> container = Container("Group")
            >>> layout.addWidget(container)
            >>> content_layout = QGridLayout(container.contentWidget)
            >>> content_layout.addWidget(QPushButton("Button"))
    """
    def __init__(self, name, color_background=False):
        """Container Class Constructor to initialize the object

        Args:
            name (str): Name for the header
            color_background (bool): whether or not to color the background lighter like in maya
        """
        super(Container, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._content_widget = QWidget()
        if color_background:
            self._content_widget.setStyleSheet(".QWidget{background-color: rgb(73, 73, 73); "
                                               "margin-left: 2px; margin-right: 2px}")
        header = Header(name, self._content_widget)
        layout.addWidget(header)
        layout.addWidget(self._content_widget)

        # assign header methods to instance attributes so they can be called outside of this class
        self.collapse = header.collapse
        self.expand = header.expand
        self.toggle = header.mousePressEvent

    @property
    def contentWidget(self):
        """Getter for the content widget

        Returns: Content widget
        """
        return self._content_widget



app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()
