# SparkFun BOSSA GUI

<p align="center">
  <a href="https://github.com/sparkfun/SparkFun_BOSSA_GUI/issues" alt="Issues">
    <img src="https://img.shields.io/github/issues/sparkfun/SparkFun_BOSSA_GUI.svg" /></a>
  <a href="https://github.com/sparkfun/SparkFun_BOSSA_GUI/actions" alt="Actions">
    <img src="https://github.com/sparkfun/SparkFun_BOSSA_GUI/actions/workflows/build-and-release.yml/badge.svg" /></a>
  <a href="https://github.com/sparkfun/SparkFun_BOSSA_GUI/blob/main/LICENSE.md" alt="License">
    <img src="https://img.shields.io/badge/license-CC%20BY--SA%204.0-EF9421.svg" /></a>
  <a href="https://twitter.com/intent/follow?screen_name=sparkfun">
    <img src="https://img.shields.io/twitter/follow/sparkfun.svg?style=social&logo=twitter" alt="follow on Twitter"></a>
</p>

[![SparkFun LoRaSerial Kit - 915MHz](./img/SparkFun_LoRaSerial_Kit.png)](https://www.sparkfun.com/products/19311)

*[SparkFun LoRaSerial Kit - 915MHz (WRL-19311)](https://www.sparkfun.com/products/19311)*

![BOSSA GUI](./img/BOSSA_GUI.png)

Our BOSSA (Basic Open Source SAM-BA Application) GUI is a convenient way to upgrade the firmware on many SAMD21 and SAMD51 boards. We wrote it to make it easy to upgrade the firmware on our
[LoRaSerial boards](https://www.sparkfun.com/products/19311), but you can use it to upload binary firmware to any board running the SAM-BA bootloader.

* The BOSSA GUI is a PyQt5 'wrapper' for the excellent Python SAM-BA Loader.
* Our GUI makes it easy to select the firmware file and COM port.
* For SAMD21, it also performs the open-port-at-1200-baud-and-toggle-DTR action to place the board into bootloader mode.
  * Note: we've had mixed success with this feature. Sometimes it works, sometimes it doesn't. It seems to be machine-dependent...
  * If it doesn't work for you, uncheck the SAMD21 check-box and double-click the board reset button to manually put the board into bootloader mode.
* For SAMD51, you need to manually double-click the reset button to put the board into bootloader mode (indicated by the fading LED) and then select the updated COM port.
* The actual upgrade is done by the Python SAM-BA Loader.
  * You can run the Loader from the command line too. See below

## BOSSA_GUI Executable

You will find the zipped BOSSA_GUI executables attached to each [release](https://github.com/sparkfun/SparkFun_BOSSA_GUI/releases).

### Windows Installation

* Download the GitHub [release](https://github.com/sparkfun/SparkFun_BOSSA_GUI/releases) zip file - *BOSSA__GUI.win.zip*
* Unzip the release file - *BOSSA__GUI.win.zip*
* This results in the application executable, *BOSSA__GUI.exe*
* Double-click *BOSSA__GUI.exe* to start the application

## Command Line

You can run the Python SAM-BA Loader direct from the command line. Download the [full repo zip file](https://github.com/sparkfun/SparkFun_BOSSA_GUI/archive/refs/heads/main.zip).
Extract it. Python SAM-BA Loader is in the ```BOSSA_GUI\SAMBALoad``` sub-folder.

* ```python SAMBALoader.py``` will display the help. So will ```python SAMBALoader.py -h``` or ```python SAMBALoader.py --help```
* ```python SAMBALoader.py -p COM1 info``` will display part information from the board on COM1 (Windows). Replace with ```/dev/ttyACM0``` if you are on Linux.
* ```python SAMBALoader.py -p COM1 erase -a 0x2000``` will erase the flash memory starting at address 0x2000 (SAMD21). Use 0x4000 for SAMD51.
* ```python SAMBALoader.py -p COM1 write -a 0x2000 -f myCode.bin``` will write ```myCode.bin``` to flash memory, starting at address 0x2000 (SAMD21).
* ```python SAMBALoader.py -p COM1 verify -a 0x2000 -f myCode.bin``` will verify the flash memory against ```myCode.bin```
* ```python SAMBALoader.py -p COM1 read -a 0x2000 -l 0x1000 -f myCode.bin``` will read 0x1000 bytes from flash memory, starting at address 0x2000 and write them into ```myCode.bin```
* Add the ```--reset``` switch to reset the board when the operation is complete. E.g. ```python SAMBALoader.py -p COM1 --reset verify -a 0x2000 -f myCode.bin```
* Add the ```-v``` switch to display helpful verbose messages. Add ```-vv``` for even more verbose messages.

## Thanks

Big thanks go to Dean Camera (@abcminiuser) and the contributors to [Python SAM-BA Loader](https://github.com/abcminiuser/sam-ba-loader).

Big thanks go to Scott Shumate (@shumatech) and the contributors to [BOSSA](https://github.com/shumatech/BOSSA).

## Repository Contents

* **[/BOSSA_GUI](./BOSSA_GUI)** - Python3 PyQt5 source (.py)
* **[/.github/workflows/build-windows.yml](./.github/workflows/build-windows.yml)** - YAML for the GitHub Build Action - for Windows
* **[/.github/workflows/non-release-build.yml](./.github/workflows/non-release-build.yml)** - YAML for the GitHub Non-Release-Build Action
  * Builds the zipped executable but does not release it
  * Click on the repo **Actions** tab and then click on the latest **non-release-build** workflow run. The zipped executable is attached as an Artifact
* **[/.github/workflows/build-and-release.yml](./.github/workflows/build-and-release.yml)** - YAML for the GitHub Build-And-Release Action
  * Builds the zipped executables, creates a release and attaches the zip files as Assets
  * Click on the [Releases](https://github.com/sparkfun/SparkFun_BOSSA_GUI/releases) and then click on the latest release. The zipped executables are attached as Assets

## License Information

This product is _**open source**_! 

Please review the LICENSE.md file for license information. 

If you have any questions or concerns on licensing, please contact technical support on our [SparkFun forums](https://forum.sparkfun.com/viewforum.php?f=152).

Distributed as-is; no warranty is given.

- Your friends at SparkFun.
