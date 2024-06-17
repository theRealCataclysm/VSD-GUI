#! /usr/bin/python
import io
import sys
import os
import re
import time
import json
import subprocess
import xml.etree.ElementTree as ET
from threading import Timer
from time import strftime, gmtime
from PySide2 import QtCore, QtGui
from PySide2.QtCore import Qt, QSize, QObject, Signal, QProcess, QByteArray, QTimer, QProcessEnvironment
from PySide2.QtWidgets import (
    QApplication,
    QTableWidgetItem,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QWidget,
    QToolBar,
    QAction,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QTabWidget,
    QTextBrowser,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QRadioButton,
    QComboBox,
    QListView,
    QPlainTextEdit,
    QTableWidget,
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
size_re = re.compile("[0-9]+.[0-9][0-9] (.*)iB / [0-9]+.[0-9][0-9] [MGK]iB")
alt_size_re = re.compile("[0-9]+.[0-9][0-9] / [0-9]+.[0-9][0-9] [MGK]iB")
time_re = re.compile("[0-9][0-9]:[0-9][0-9] > [0-9][0-9]:[0-9][0-9]")
mbspeed_re = re.compile("[0-9].[0-9][0-9] [MGK]iB/s")
seg_re = re.compile("[0-9]+/[0-9]+")
segspeed_re = re.compile("[0-9]+.[0-9]+ SEG/s")
dfilename_re = re.compile("vsd_(.*)$")
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

def video_link_locator(self, output):
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
        pc_complete = m.group()
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
        self.CaptureRefreshButton.clicked.connect(lambda: self.p.kill())
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
        self.DownloadRefreshButton.clicked.connect(lambda: self.p.kill())
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
        self.downloadQuality.addItems(["Select", "Lowest", "Highest"])

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
        #self.captureQueueView = QListView()
        #tab2.layout6.addWidget(self.captureQueueView)
        #self.captureQueueView.setModel(self.capturemodel)
        #self.captureQueueView.setModelColumn(0)

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
        #self.downloadQueueView = QListView()
        #tab3.layout5.addWidget(self.downloadQueueView)
        #self.downloadQueueView.setModel(self.downloadmodel)
        #self.downloadQueueView.setModelColumn(0)
        #self.downloadQueueView.setSelectionBehavior(QTableView.SelectRows)
        #self.downloadQueueView.doubleClicked.connect(lambda: self.selectdownload())

        downloadbuttonbox1 = QWidget()
        tab3.layout.addWidget(downloadbuttonbox1, 0, 1)
        downloadbuttonbox1.setLayout(tab3.layout6)
        downloadbuttonbox1.setContentsMargins(0, 0, 0, 0)
        self.DownloadStartButton = QPushButton("Download")
        tab3.layout6.addWidget(self.DownloadStartButton)
        self.DownloadStartButton.clicked.connect(
            lambda: self.start_download(self.downloadText2.text()))
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

        self.show()

    def clearCapture(self):
        self.captureText2.setText("")
        self.captureparseName.setText("")

    def clearDownload(self):
        self.downloadText2.setText("")
        self.downloadparseName.setText("")

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
                self.downloadQuality.setCurrentIndex(2)
            elif q == 'Lowest':
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

    def message(self, s):
        self.statustext.appendPlainText(s)


    def handle_stderr(self):
        errdata = self.p.readAllStandardError()
        errbytes = QByteArray(errdata)
        strstderr = str(errbytes)
        stderr = strstderr.strip()
        # stderr = bytes(errdata).decode("utf-8", errors="ignore")
        downloadtime = download_time(stderr)
        if downloadtime:
            dtime = str(downloadtime)
            self.downloadtimedsp.setText(dtime)
        downloadsize = download_size(stderr)
        if downloadsize:
            dsize = str(downloadsize)
            self.downloadsizedsp.setText(dsize)
        downloadmbspeed = download_mbspeed(stderr)
        if downloadmbspeed:
            dmb = str(downloadmbspeed)
            self.downloadmbspeeddsp.setText(dmb)
        downloadsegs = download_seg(stderr)
        if downloadsegs:
            dsegs = str(downloadsegs)
            self.downloadsegsdsp.setText(dsegs)
        downloadsegspeed = download_segpeed(stderr)
        if downloadsegspeed:
            dseg = str(downloadsegspeed)
            self.downloadsegspeeddsp.setText(dseg)
        dfilename = download_filename(stderr)
        if dfilename:
            dfile = dfilename[:-217]
            fname = dict(filename=dfile)
            with open("download_temp.json", "w") as f:
                linkf = json.dump(fname, f)
            self.message("File Name: " + dfile)
        progress = simple_percent_parser(stderr)
        if progress:
            self.progressBar1.setValue(progress)
            self.progressBar2.setValue(progress)
            self.progressBar3.setValue(progress)
            self.progressBar4.setValue(progress)

        #self.message(stderr)

    def handle_stdout(self):
        outdata = self.p.readAllStandardOutput()
        outbytes = QByteArray(outdata)
        strstdout = str(outbytes)
        stdout = strstdout.rstrip()
        #stdout = bytes(prestdout).decode("utf-8", errors="ignore")
        downloadlinks = video_link_locator(self, stdout)
        init = capture_init(stdout)
        if init:
            self.t = QTimer()
            self.t.setInterval(5000)
            self.t.timeout.connect(self.timeout)
            if not self.t.isActive():
                self.t.start()
                self.message("Starting Timer!")
        if downloadlinks:
            linkpass1 = downloadlinks.replace("Detected ", "")
            link = linkpass1[:-3]
            self.links.append(dict(link=link))
            with open("out_temp.json", "w") as f:
                linkf = json.dump(self.links, f)
            self.message(link)
            self.t.stop()
            if not self.t.isActive():
                self.t.start(2500)
                self.message("Restarting Timer!")

    def timeout(self):
        if self.p:
            self.p.kill()
            self.message("Timed Out!")
        self.t.stop()
        dlg = QualitySelectDialog()
        dlg.open()
        #os.rename(fn, 'b.mp4')

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
        self.StartButton.setEnabled(True),
        self.CaptureStartButton.setEnabled(True)
        self.DownloadStartButton.setEnabled(True)
        self.CaptureCancelButton.setEnabled(False)
        self.DownloadCancelButton.setEnabled(False)
        self.progressBar1.setVisible(False)
        self.progressBar2.setVisible(False)
        self.progressBar3.setVisible(False)
        self.progressBar4.setVisible(False)
        self.downloadtimedsp.setVisible(False)
        self.downloadsizedsp.setVisible(False)
        self.downloadmbspeeddsp.setVisible(False)
        self.downloadsegsdsp.setVisible(False)
        self.downloadsegspeeddsp.setVisible(False)

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
            self.p.setProcessEnvironment(self.env)
            self.p.start("vsd capture --color never " + URL)
            self.StartButton.setEnabled(False),
            self.CaptureStartButton.setEnabled(False)
            self.DownloadStartButton.setEnabled(False)
            self.CaptureCancelButton.setEnabled(True)

    def start_download(self, URL):
        if self.p is None:  # No process running.
            self.message("Starting Download")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.env = QProcessEnvironment.systemEnvironment()
            self.env.insert("KDAM_NCOLS", "0") # Remove Progress bar
            self.p.setProcessEnvironment(self.env)

            self.p.start("vsd save --color never " + URL)
            self.StartButton.setEnabled(False),
            self.CaptureStartButton.setEnabled(False)
            self.DownloadStartButton.setEnabled(False)
            self.DownloadCancelButton.setEnabled(True)
            self.progressBar1.setVisible(True)
            self.progressBar2.setVisible(True)
            self.progressBar3.setVisible(True)
            self.progressBar4.setVisible(True)
            self.downloadtimedsp.setVisible(True)
            self.downloadsizedsp.setVisible(True)
            self.downloadmbspeeddsp.setVisible(True)
            self.downloadsegsdsp.setVisible(True)
            self.downloadsegspeeddsp.setVisible(True)


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
        if Q == 2:
            q = "Highest"
        elif Q == 1:
            q = "Lowest"
        else:
            q = "Select"
        c = dict(cid=k, url=u, quality=q, option=o, filename=f)

        with open("capture_temp.json", "w") as f:
            linkf = json.dump(c, f)
        self.start_capture(u)

    def DownloadNow(URL, File):
        if File:
            subprocess.run("vsd save --output " + str(File) + " " + str(URL), shell=True)
        else:
            subprocess.run("vsd save " + str(URL), shell=True)

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
        if Q == 2:
            Quality = "Highest"
        elif Q == 1:
            Quality = "Lowest"
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
        MainWindow.downloads = d
        #MainWindow.downloadmodel.layoutChanged.emit()

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
        selectButton.clicked.connect(lambda: self.add2Queue())
    def loadDownloads(self):
        try:
            with open("downloads.json", "r") as f:
                self.downloads = json.load(f)
        except Exception:
            self.downloads = []
            pass

    def add2Queue(self):
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
        k = cd['cid']
        o = cd['option']
        f = cd['filename']
        if f == '':
            o = "None"
            f = "None"
        # print('cid=' + k + ', url=' + u +', option=' + o + ', filename=' + f)
        self.downloadmodel.appendRow(k, u, o, f)
        # self.downloadmodel.layoutChanged.emit()
        MainWindow.refresh_downloads(self.downloads)
        self.close()

class PreferencesDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Preferences")



app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()
