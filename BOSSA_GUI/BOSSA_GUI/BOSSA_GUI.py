"""
This is a simple Python3 PyQt5 wrapper for Dean Camera (@abcminiuser)'s sam-ba-loader:
https://github.com/abcminiuser/sam-ba-loader

MIT license

Please see the LICENSE.md for more details

"""

# import action things - the .syntax is used since these are part of the package
from .au_worker import AUxWorker
from .au_action import AxJob
from .au_act_samba_loader import AUxSAMBADetect, AUxSAMBAErase, AUxSAMBAProgram, AUxSAMBAVerify, AUxSAMBAReset

import darkdetect
import sys
import os
import os.path
import platform

import serial
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE
import time

from typing import Iterator, Tuple

from PyQt5.QtCore import QSettings, QProcess, QTimer, Qt, QIODevice, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit, \
    QAction, QActionGroup, QMenu, QMenuBar, QMainWindow, QMessageBox, \
    QCheckBox
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPortInfo

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
SETTING_ERASE = 'erase'
SETTING_VERIFY = 'verify'
SETTING_SAMD21 = 'samd21'

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

#----------------------------------------------------------------
# ux_is_darkmode()
#
# Helpful function used during setup to determine if the Ux is in
# dark mode
_is_darkmode = None
def ux_is_darkmode() -> bool:
    global _is_darkmode

    if _is_darkmode is not None:
        return _is_darkmode

    osName = platform.system()

    if osName == "Darwin":
        _is_darkmode = darkdetect.isDark()

    elif osName == "Windows":
        # it appears that the Qt interface on Windows doesn't apply DarkMode
        # So, just keep it light
        _is_darkmode = False
    elif osName == "Linux":
        # Need to check this on Linux at some pont
        _is_darkmod = False

    else:
        _is_darkmode = False

    return _is_darkmode

# noinspection PyArgumentList

class MainWidget(QWidget):
    """Main Widget."""

    sig_message = pyqtSignal(str)
    sig_finished = pyqtSignal(int, str, int, str, int)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.processor = '' # Will be detected

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

        # Erase Check Box
        self.erase_checkbox = QCheckBox(self.tr('Erase'))
        self.erase_checkbox.setChecked(False)

        # Verify Check Box
        self.verify_checkbox = QCheckBox(self.tr('Verify'))
        self.verify_checkbox.setChecked(False)

        # SAMD21 Check Box
        self.samd21_checkbox = QCheckBox(self.tr('SAMD21'))
        self.samd21_checkbox.setChecked(False)

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
        color =  "C0C0C0" if ux_is_darkmode() else "424242"
        self.messageBox.setStyleSheet("QPlainTextEdit { color: #" + color + ";}")
        self.messageBox.setReadOnly(True)
        self.messageBox.clear()

        # Arrange Layout
        layout = QGridLayout()
        
        layout.addWidget(self.firmware_label, 1, 0)
        layout.addWidget(self.firmwareLocation_lineedit, 1, 1)
        layout.addWidget(self.firmware_browse_btn, 1, 3)

        layout.addWidget(self.port_label, 2, 0)
        layout.addWidget(self.port_combobox, 2, 1)

        layout.addWidget(self.erase_checkbox, 2, 3)
        layout.addWidget(self.verify_checkbox, 3, 3)
        layout.addWidget(self.samd21_checkbox, 4, 3)

        layout.addWidget(self.messages_label, 5, 0)
        layout.addWidget(self.upload_btn, 5, 2, 1, 2)
        layout.addWidget(self.messageBox, 6, 0, 4, 4)

        self.setLayout(layout)

        self.settings = QSettings()
        #self._clean_settings() # This will delete all existing settings! Use with caution!
        self._load_settings()

        self.setWindowTitle( _APP_NAME + " - " + _APP_VERSION)

        # setup our background worker thread ...

        # connect the signals from the background processor to callback
        # methods/slots. This makes it thread safe
        self.sig_message.connect(self.writeMessage)
        self.sig_finished.connect(self.on_finished)

        # Create our background worker object, which also will do work in it's
        # own thread.
        self._worker = AUxWorker(self.on_worker_callback)

        # add the actions/commands for this app to the background processing thread.
        # These actions are passed jobs to execute.
        self._worker.add_action(AUxSAMBADetect(), AUxSAMBAErase(), AUxSAMBAProgram(), AUxSAMBAVerify(), AUxSAMBAReset())

    #--------------------------------------------------------------
    # callback function for the background worker.
    #
    # It is assumed that this method is called by the background thread
    # so signals and used to relay the call to the GUI running on the
    # main thread

    def on_worker_callback(self, *args): #msg_type, arg):

        # need a min of 2 args (id, arg)
        if len(args) < 2:
            self.writeMessage("Invalid parameters from the SAMBALoader.")
            return

        msg_type = args[0]
        if msg_type == AUxWorker.TYPE_MESSAGE:
            self.sig_message.emit(args[1])
        elif msg_type == AUxWorker.TYPE_FINISHED:
            # finished takes 3 args - status, job type, job id and message
            if len(args) < 6:
                self.writeMessage("Invalid parameters from the SAMBALoader.");
                return;

            self.sig_finished.emit(args[1], args[2], args[3], args[4], args[5])
            
    @pyqtSlot(str)
    def writeMessage(self, msg) -> None:
        self.messageBox.moveCursor(QTextCursor.End)
        self.messageBox.ensureCursorVisible()
        self.messageBox.appendPlainText(msg)
        self.messageBox.ensureCursorVisible()
        self.messageBox.repaint()

    @pyqtSlot(str)
    def insertPlainText(self, msg) -> None:
        if msg.startswith("\r"):
            self.messageBox.moveCursor(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            self.messageBox.cut()
            self.messageBox.insertPlainText(msg[1:])
        else:
            self.messageBox.insertPlainText(msg)
        self.messageBox.ensureCursorVisible()
        self.messageBox.repaint()


    #--------------------------------------------------------------
    # on_finished()
    #
    #  Slot for sending the "on finished" signal from the background thread
    #
    #  Called when the backgroudn job is finished and includes a status value
    @pyqtSlot(int, str, int, str, int)
    def on_finished(self, status, action_type, job_id, job_message, job_sysExit) -> None:

        # If the part detection is finished, trigger the erase / program
        if action_type == AUxSAMBADetect.ACTION_ID:
            self.processor = job_message
            if job_sysExit > 0:
                self.writeMessage("Part detection failed!")
                self.disable_interface(False)
            elif self.erase:
                self.writeMessage("Part detection complete. Erasing...")
                self.do_erase()
            else:
                self.writeMessage("Part detection complete. Programming...")
                self.do_program()

        # If the erase is finished, trigger the program
        elif action_type == AUxSAMBAErase.ACTION_ID:
            if job_sysExit > 0:
                self.writeMessage("Erase failed!")
                self.disable_interface(False)
            else:
                self.writeMessage("Erase complete. Programming...")
                self.do_program()

        # If the program is finished, trigger the verify / reset
        elif action_type == AUxSAMBAProgram.ACTION_ID:
            if job_sysExit > 0:
                self.writeMessage("Program failed!")
                self.disable_interface(False)
            elif self.verify:
                self.writeMessage("Program complete. Verifying...")
                self.do_verify()
            else:
                self.writeMessage("Program complete. Resetting...")
                self.do_reset()

        # If the verify is finished, trigger the reset
        elif action_type == AUxSAMBAVerify.ACTION_ID:
            if job_sysExit > 0:
                self.writeMessage("Verify failed!")
                self.disable_interface(False)
            else:
                self.writeMessage("Verify complete. Resetting...")
                self.do_reset()

        # re-enable the UX
        else:
            self.writeMessage("Complete...")
            self.disable_interface(False)

    def _load_settings(self) -> None:
        """Load settings on startup."""
        port_name = self.settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        lastFile = self.settings.value(SETTING_FIRMWARE_LOCATION)
        if lastFile is not None:
            self.firmwareLocation_lineedit.setText(lastFile)

        check_state = self.settings.value(SETTING_ERASE)
        if check_state is not None:
            trueFalse = True if check_state == "True" else False
            self.erase_checkbox.setChecked(trueFalse)

        check_state = self.settings.value(SETTING_VERIFY)
        if check_state is not None:
            trueFalse = True if check_state == "True" else False
            self.verify_checkbox.setChecked(trueFalse)

        check_state = self.settings.value(SETTING_SAMD21)
        if check_state is not None:
            trueFalse = True if check_state == "True" else False
            self.samd21_checkbox.setChecked(trueFalse)
            

    def _save_settings(self) -> None:
        """Save settings on shutdown."""
        self.settings.setValue(SETTING_PORT_NAME, self.port)
        self.settings.setValue(SETTING_FIRMWARE_LOCATION, self.theFirmwareName)
        trueFalse = "True" if self.erase else "False"
        self.settings.setValue(SETTING_ERASE, trueFalse)
        trueFalse = "True" if self.verify else "False"
        self.settings.setValue(SETTING_VERIFY, trueFalse)
        trueFalse = "True" if self.samd21 else "False"
        self.settings.setValue(SETTING_SAMD21, trueFalse)

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

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return str(self.port_combobox.currentData())

    @property
    def theFirmwareName(self) -> str:
        """Return the firmware file name."""
        return self.firmwareLocation_lineedit.text()

    @property
    def erase(self) -> str:
        """Return the erase check box."""
        return self.erase_checkbox.isChecked()

    @property
    def verify(self) -> str:
        """Return the verify check box."""
        return self.verify_checkbox.isChecked()

    @property
    def samd21(self) -> str:
        """Return the samd21 check box."""
        return self.samd21_checkbox.isChecked()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        try:
            self._save_settings()
        except:
            pass

        # shutdown the background worker/stop it so the app exits correctly
        self._worker.shutdown()

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

    #--------------------------------------------------------------
    # disable_interface()
    #
    # Enable/Disable portions of the ux - often used when a job is running
    #
    def disable_interface(self, bDisable=False):

        self.upload_btn.setDisabled(bDisable)

    def on_upload_btn_pressed(self) -> None:
        """Update the firmware"""

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

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

        self.portActual = self.port

        if self.samd21:

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

                if self.portActual not in portsAfter:
                    #self.writeMessage("Hey! " + str(self.portActual) + " disappeared!")
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
                        self.portActual = portSys
                        keepGoing = False
                        break

                    if (portSys == self.portActual) and portGone:
                        #self.writeMessage("Hey! " + str(portSys) + " came back again!")
                        self.portActual = portSys
                        keepGoing = False
                        break

                if keepGoing:
                    time.sleep(0.25)

            if keepGoing:
                self.writeMessage("Port has not changed. Trying " + self.portActual)
            else:
                self.writeMessage("Port has changed. Using " + self.portActual)

        else:

            self.writeMessage("\nAssuming SAMD51 is already in bootloader mode (fading LED)\n")

        self.writeMessage("\nDetecting processor\n")

        command = []
        command.extend(["-p",self.portActual])
        command.append("info")

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxSAMBADetect.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def do_erase(self) -> None:
        """Erase the processor"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.portActual):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            self.disable_interface(False)
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        sleep(1.0);
        self.writeMessage("Erasing processor\n")

        command = []
        command.extend(["-p",self.portActual])
        command.append("erase")

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxSAMBAErase.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def do_program(self) -> None:
        """Program the firmware"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.portActual):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            self.disable_interface(False)
            return

        fileExists = False
        try:
            f = open(self.theFileName)
            fileExists = True
        except IOError:
            fileExists = False
        finally:
            if (fileExists == False):
                self.writeMessage("File Not Found")
                self.disable_interface(False)
                return
            f.close()

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        sleep(1.0);
        self.writeMessage("Uploading firmware\n")

        command = []
        command.extend(["-p",self.portActual])
        command.append("write")
        if "SAMD21" in self.processor:
            command.extend(["-a","0x2000"])
        elif "SAMD51" in self.processor:
            command.extend(["-a","0x4000"])
        command.extend(["-f",self.theFileName])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxSAMBAProgram.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True) # Redundant... Interface is still disabled from flash detect

    def do_verify(self) -> None:
        """Verify the firmware"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.portActual):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            self.disable_interface(False)
            return

        fileExists = False
        try:
            f = open(self.theFileName)
            fileExists = True
        except IOError:
            fileExists = False
        finally:
            if (fileExists == False):
                self.writeMessage("File Not Found")
                self.disable_interface(False)
                return
            f.close()

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        sleep(1.0);
        self.writeMessage("Verifying firmware\n")

        command = []
        command.extend(["-p",self.portActual])
        command.append("verify")
        if "SAMD21" in self.processor:
            command.extend(["-a","0x2000"])
        elif "SAMD51" in self.processor:
            command.extend(["-a","0x4000"])
        command.extend(["-f",self.theFileName])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxSAMBAVerify.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True) # Redundant... Interface is still disabled from flash detect

    def do_reset(self) -> None:
        """Reset the processor"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.portActual):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            self.disable_interface(False)
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        sleep(1.0);
        self.writeMessage("Resetting processor\n")

        command = []
        command.extend(["-p",self.portActual])
        command.extend(["--reset","info"])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxSAMBAReset.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

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
