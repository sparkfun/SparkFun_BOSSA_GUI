"""
This is a simple Python3 PyQt5 wrapper for Scott Shumate's bossac.exe.
https://github.com/shumatech/BOSSA
The actual read/write/verify is done by bossac.exe.

bossac.exe is a Windows executable. This tool will only work on Windows. Sorry about that.
Version 1.9.1-17-g89f3556, copied from Arduino15\packages\arduino\tools\bossac\v1.9.1-arduino2

MIT license

Please see the LICENSE.md for more details

"""

from typing import Iterator, Tuple

from PyQt5.QtCore import QSettings, QProcess, QTimer, Qt, QIODevice, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit, \
    QAction, QActionGroup, QMenu, QMenuBar, QMainWindow, QMessageBox, \
    QCheckBox
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPortInfo

import sys
import os

import serial
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE
import time

_APP_NAME = "BOSSA GUI"

# sub folder for our resource files
_RESOURCE_DIRECTORY = "resource"

#https://stackoverflow.com/a/50914550
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, _RESOURCE_DIRECTORY, relative_path)

def get_version(rel_path: str) -> str:
    try: 
        with open(resource_path(rel_path), encoding='utf-8') as fp:
            for line in fp.read().splitlines():
                if line.startswith("__version__"):
                    delim = '"' if '"' in line else "'"
                    return line.split(delim)[1]
            raise RuntimeError("Unable to find version string.")
    except:
        raise RuntimeError("Unable to find _version.py.")

_APP_VERSION = get_version("_version.py")

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_FIRMWARE_LOCATION = 'firmware_location'
SETTING_OFFSET = 'offset'

# ----------------------------------------------------------------
# hack to know when a combobox menu is being shown. Helpful if contents
# of list are dynamic -- like serial ports.
class AUxComboBox(QComboBox):

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super().showPopup()

def gen_serial_ports() -> Iterator[Tuple[str, str, str]]:
    """Return all available serial ports."""
    ports = QSerialPortInfo.availablePorts()
    return ((p.description(), p.portName(), p.systemLocation()) for p in ports)

# noinspection PyArgumentList

class MainWidget(QWidget):
    """Main Widget."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.p = None # This will be the updater QProcess

        # Firmware file location line edit
        self.firmware_label = QLabel(self.tr('Binary File:'))
        self.firmwareLocation_lineedit = QLineEdit()
        self.firmware_label.setBuddy(self.firmwareLocation_lineedit)
        self.firmwareLocation_lineedit.setEnabled(False)
        self.firmwareLocation_lineedit.returnPressed.connect(
            self.on_browse_firmware_btn_pressed)

        # Browse for new file button
        self.firmware_browse_btn = QPushButton(self.tr('Browse'))
        self.firmware_browse_btn.setEnabled(True)
        self.firmware_browse_btn.pressed.connect(self.on_browse_firmware_btn_pressed)

        # Port Combobox
        self.port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = AUxComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.update_com_ports()
        self.port_combobox.popupAboutToBeShown.connect(self.on_port_combobox)

        # Offset Combobox
        self.offset_label = QLabel(self.tr('Offset:'))
        self.offset_combobox = QComboBox()
        self.offset_label.setBuddy(self.offset_combobox)
        self.update_offsets()

        # Upload Button
        myFont=QFont()
        myFont.setBold(True)
        self.upload_btn = QPushButton(self.tr('Upload Binary'))
        self.upload_btn.setFont(myFont)
        self.upload_btn.clicked.connect(self.on_upload_btn_pressed)

        # Messages Bar
        self.messages_label = QLabel(self.tr('Status / Warnings:'))

        # Messages Window
        messageFont=QFont("Courier")
        self.messageBox = QPlainTextEdit()
        self.messageBox.setFont(messageFont)

        # Arrange Layout
        layout = QGridLayout()
        
        layout.addWidget(self.firmware_label, 1, 0)
        layout.addWidget(self.firmwareLocation_lineedit, 1, 1)
        layout.addWidget(self.firmware_browse_btn, 1, 3)

        layout.addWidget(self.port_label, 2, 0)
        layout.addWidget(self.port_combobox, 2, 1)

        layout.addWidget(self.offset_label, 3, 0)
        layout.addWidget(self.offset_combobox, 3, 1)

        layout.addWidget(self.messages_label, 4, 0)
        layout.addWidget(self.upload_btn, 4, 2, 1, 2)
        layout.addWidget(self.messageBox, 5, 0, 4, 4)

        self.setLayout(layout)

        self.settings = QSettings()
        #self._clean_settings() # This will delete all existing settings! Use with caution!
        self._load_settings()

    def writeMessage(self, msg) -> None:
        self.messageBox.moveCursor(QTextCursor.End)
        self.messageBox.ensureCursorVisible()
        self.messageBox.appendPlainText(msg)
        self.messageBox.ensureCursorVisible()
        self.messageBox.repaint()
        QApplication.processEvents()

    def insertPlainText(self, msg) -> None:
        if msg.startswith("\r"):
            self.messageBox.moveCursor(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            self.messageBox.cut()
            self.messageBox.insertPlainText(msg[1:])
        else:
            self.messageBox.insertPlainText(msg)
        self.messageBox.ensureCursorVisible()
        self.messageBox.repaint()
        QApplication.processEvents()


    def _load_settings(self) -> None:
        """Load settings on startup."""
        port_name = self.settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        offset_name = self.settings.value(SETTING_OFFSET)
        if offset_name is not None:
            index = self.offset_combobox.findText(offset_name)
            if index > -1:
                self.offset_combobox.setCurrentIndex(index)

        lastFile = self.settings.value(SETTING_FIRMWARE_LOCATION)
        if lastFile is not None:
            self.firmwareLocation_lineedit.setText(lastFile)

    def _save_settings(self) -> None:
        """Save settings on shutdown."""
        self.settings.setValue(SETTING_PORT_NAME, self.port)
        self.settings.setValue(SETTING_OFFSET, self.offset)
        self.settings.setValue(SETTING_FIRMWARE_LOCATION, self.theFirmwareName)

    def _clean_settings(self) -> None:
        """Clean (remove) all existing settings."""
        self.settings.clear()

    def show_error_message(self, msg: str) -> None:
        """Show a Message Box with the error message."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    def show_warning_message(self, msg: str) -> None:
        """Show a Message Box with the warning."""
        QMessageBox.warning(self, QApplication.applicationName(), str(msg))

    # --------------------------------------------------------------
    # on_port_combobox()
    #
    # Called when the combobox pop-up menu is about to be shown
    #
    # Use this event to dynamically update the displayed ports
    #
    @pyqtSlot()
    def on_port_combobox(self):
        self.update_com_ports()

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""

        previousPort = self.port # Record the previous port before we clear the combobox
        
        self.port_combobox.clear()

        index = 0
        indexOfPrevious = -1
        for desc, name, sys in gen_serial_ports():
            longname = desc + " (" + name + ")"
            self.port_combobox.addItem(longname, sys)
            if(sys == previousPort): # Previous port still exists so record it
                indexOfPrevious = index
            index = index + 1

        if indexOfPrevious > -1: # Restore the previous port if it still exists
            self.port_combobox.setCurrentIndex(indexOfPrevious)

    def update_offsets(self) -> None:
        """Update memory offset list in GUI."""

        previousOffset = self.offset # Record the previous offset before we clear the combobox
        
        self.offset_combobox.clear()

        index = 0
        indexOfPrevious = -1
        for offset in ["0x2000 (SAMD21)", "0x4000 (SAMD51)"]:
            self.offset_combobox.addItem(offset)
            if(offset == previousOffset): # Previous offset still exists so record it
                indexOfPrevious = index
            index = index + 1

        if indexOfPrevious > -1: # Restore the previous offset if it still exists
            self.offset_combobox.setCurrentIndex(indexOfPrevious)

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return str(self.port_combobox.currentData())

    @property
    def offset(self) -> str:
        """Return the current offset."""
        return str(self.offset_combobox.currentText())

    @property
    def theFirmwareName(self) -> str:
        """Return the firmware file name."""
        return self.firmwareLocation_lineedit.text()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        try:
            self._save_settings()
        except:
            pass

        event.accept()

    def on_browse_firmware_btn_pressed(self) -> None:
        """Open dialog to select firmware file."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Select Binary File to Upload",
            self.theFirmwareName,
            "Binary Files (*.bin);;All Files (*)",
            options=options)
        if fileName:
            self.firmwareLocation_lineedit.setText(fileName)

    def update_finished(self) -> None:
        """The update QProcess has finished."""
        self.writeMessage("Upload has finished")
        self.p = None

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.insertPlainText(stderr)

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.insertPlainText(stdout)

    def on_upload_btn_pressed(self) -> None:
        """Update the firmware"""

        self.writeMessage("\n")

        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        firmwareExists = False
        try:
            f = open(self.theFirmwareName)
            firmwareExists = True
        except IOError:
            firmwareExists = False
        finally:
            if (firmwareExists == False):
                self.writeMessage("Binary File Not Found")
                return
            f.close()

        if self.p is not None:
            self.writeMessage("Upload is already running")
            return

        portActual = self.port

        if self.offset.find("SAMD21") >= 0:

            # Open the port at 1200 baud to enter the bootloader
            # See touchForCDCReset in:
            # https://github.com/arduino/Arduino/blob/master/arduino-core/src/processing/app/Serial.java
            self.writeMessage("\nEnter SAMD21 bootloader\n")

            portsBefore = []
            for desc, name, sys in gen_serial_ports():
                portsBefore.append(sys)

            try:
                port = serial.Serial(self.port, baudrate=1200, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=0)
            except (ValueError, IOError) as err:
                self.writeMessage(str(err))
                return

            port.setDTR(False) # Reset the SAMD
            port.close()

            time.sleep(0.4)

            startTime = time.time()
            keepGoing = True
            portGone = False

            # For up to three seconds: wait for the port to disappear
            while keepGoing and (time.time() < (startTime + 3.0)):

                portsAfter = []
                for desc, name, sys in gen_serial_ports():
                    portsAfter.append(sys)

                if portActual not in portsAfter:
                    #self.writeMessage("Hey! " + str(portActual) + " disappeared!")
                    portGone = True
                    keepGoing = False
                else:
                    time.sleep(0.25)

            time.sleep(0.25)

            startTime = time.time()
            keepGoing = True

            # For up to three seconds: keep checking the available ports to see if a new one pops up, or the old one reappears
            # If no new port appears, try self.port
            while keepGoing and (time.time() < (startTime + 3.0)):

                portsAfter = []
                for desc, name, sys in gen_serial_ports():
                    portsAfter.append(sys)

                for portSys in portsAfter:
                    if portSys not in portsBefore:
                        #self.writeMessage("Hey! Found new port " + str(portSys))
                        portActual = portSys
                        keepGoing = False
                        break

                    if (portSys == portActual) and portGone:
                        #self.writeMessage("Hey! " + str(portSys) + " came back again!")
                        portActual = portSys
                        keepGoing = False
                        break

                if keepGoing:
                    time.sleep(0.25)

            if keepGoing:
                self.writeMessage("Port has not changed. Trying " + portActual)
            else:
                self.writeMessage("Port has changed. Using " + portActual)

        else:

            self.writeMessage("\nAssuming SAMD51 is already in bootloader mode (fading LED)\n")

        self.writeMessage("\nUploading binary\n")

        command = []

        command.extend(["-i","-d"])

        command.append("--port=" + portActual)

        command.append("-U")

        offsetText = self.offset
        spacePos = offsetText.find(' ')
        if spacePos >= 0:
            offsetText = offsetText[:spacePos]
        else:
            offsetText = "0x2000"
        command.append("--offset=" + offsetText)

        command.extend(["-e","-w","-v"])

        command.append(self.theFirmwareName)

        command.extend(["-R"])

        self.writeMessage("bossac.exe %s\n\n" % " ".join(command))

        if 1: # Change this to 0 to skip the actual update
            self.p = QProcess()
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.finished.connect(self.update_finished)
            self.p.start(resource_path("bossac.exe"), command)

def startGUI():
    """Start the GUI"""
    from sys import exit as sysExit
    app = QApplication([])
    app.setOrganizationName('SparkFun Electronics')
    app.setApplicationName(_APP_NAME + ' - ' + _APP_VERSION)
    app.setWindowIcon(QIcon(resource_path("sfe_logo_sm.png")))
    app.setApplicationVersion(_APP_VERSION)
    w = MainWidget()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    startGUI()
