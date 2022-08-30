# SparkFun BOSSA GUI

<p align="center">
  <a href="https://github.com/sparkfun/SparkFun_BOSSA_GUI/issues" alt="Issues">
    <img src="https://img.shields.io/github/issues/sparkfun/SparkFun_BOSSA_GUI.svg" /></a>
  <a href="https://github.com/sparkfun/SparkFun_BOSSA_GUI/actions" alt="Actions">
    <img src="https://github.com/sparkfun/SparkFun_BOSSA_GUI/actions/workflows/build.yml/badge.svg" /></a>
  <a href="https://github.com/sparkfun/SparkFun_BOSSA_GUI/blob/main/LICENSE.md" alt="License">
    <img src="https://img.shields.io/badge/license-CC%20BY--SA%204.0-EF9421.svg" /></a>
  <a href="https://twitter.com/intent/follow?screen_name=sparkfun">
    <img src="https://img.shields.io/twitter/follow/sparkfun.svg?style=social&logo=twitter" alt="follow on Twitter"></a>
</p>

[![SparkFun LoRaSerial Kit - 915MHz](./img/SparkFun_LoRaSerial_Kit.png)](https://www.sparkfun.com/products/19311)

*[SparkFun LoRaSerial Kit - 915MHz (WRL-19311)](https://www.sparkfun.com/products/19311)*

![BOSSA GUI](./img/BOSSA_GUI.png)

Our BOSSA GUI is a convenient way to upgrade the firmware on many SAMD21 and SAMD51 boards. We wrote it to make it easy to upgrade the firmware on our
[LoRaSerial boards](https://www.sparkfun.com/products/19311), but you can use it to upload binary firmware to any board running the BOSSA bootloader.

* The BOSSA GUI is a PyQt5 'wrapper' for the excellent BOSSAC command line programming utility (bossac.exe).
* Our GUI makes it easy to select the firmware file, COM port and memory offset for SAMD21 and SAMD51.
* For SAMD21, it also performs the open-port-at-1200-baud-and-toggle-DTR action to place the board into bootloader mode.
* For SAMD51, you need to manually double-click the reset button to put the board into bootloader mode (indicated by the fading LED) and then select the COM port.
* The actual upgrade is done by the bossac executable - version 1.9.1-17-g89f3556.
* We are using the pre-built bossac Windows executable, so the GUI currently only runs on Windows. Sorry about that.

## BOSSA_GUI Executable

You will find the BOSSA_GUI executable in the [Windows_exe folder](./Windows_exe).

## Thanks

Big thanks go to Scott Shumate (@shumatech) and the contributors to [BOSSA](https://github.com/shumatech/BOSSA).

## Repository Contents

* **[/Windows_exe](./Windows_exe)** - Windows executable (.exe)
* **[/BOSSA_GUI](./BOSSA_GUI)** - Python3 PyQt5 source (.py)
* **[/.github/workflows/build.yml](./.github/workflows/build.yml)** - YAML for the GitHub Build Action - based on [this how-to](https://data-dive.com/multi-os-deployment-in-cloud-using-pyinstaller-and-github-actions)

## License Information

This product is _**open source**_! 

Please review the LICENSE.md file for license information. 

If you have any questions or concerns on licensing, please contact technical support on our [SparkFun forums](https://forum.sparkfun.com/viewforum.php?f=152).

Distributed as-is; no warranty is given.

- Your friends at SparkFun.
