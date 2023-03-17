#
#      Open Source SAM-BA Programmer
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from . import Part
from . import CortexM3_4
from ..FlashControllers import NVMCTRL_D5x


class ATSAMD51(CortexM3_4):
	"""Part class for all SAMD51 based parts.
	"""

	# Define flash base etc. for SAMD51
	BOOTLOADER_SIZE    = 4096
	FLASH_BASE_ADDRESS = 0x00000000
	FLASH_APP_ADDRESS  = FLASH_BASE_ADDRESS + BOOTLOADER_SIZE

	def __init__(self, samba):
		"""Initializes class
		"""
		CortexM3_4.__init__(self, samba)
		self.flash_controllers = (
			NVMCTRL_D5x(0x41004000),
			)
		self.reset_controller = self.reset

	@staticmethod
	def identify(ids):
		"""Determines if the given chip identifiers positively identify a SAMD51
		   series device.

		Args:
			id_name   -- Name of the chip identifier being tested.
			id_values -- Chip identifier values extracted from the part.

		Returns:
			`True` if the given identifiers suggest the part is a SAMD51
			series device.
		"""
		
		result = False
		try:
			id_values = ids['DSU']
			result = id_values.processor == 6 and id_values.family == 0 and id_values.series == 6
		except:
			return False
		return result

	def reset(self):
		"""Reset the chip
		"""

		self.samba.write_word(0xE000ED0C, 0x05FA0004) # This is the way bossa does it

	def erase_chip(self, address=None):
		"""Erases the flash plane or chip.

		Args:
			address -- Address of flash plane to erase (or chip erase if `None`).
		"""

		if address is None:
			address = ATSAMD51.FLASH_APP_ADDRESS

		return self.flash_controllers[0].erase_flash(self.samba, address)

	def program_flash(self, data, address=None):
		"""Program's the device's application area.

		Args:
			data    -- Data to program into the device.
			address -- Address to program from (or start of application area if `None`).
		"""

		if address is None:
			address = ATSAMD51.FLASH_APP_ADDRESS

		return self.flash_controllers[0].program_flash(self.samba, address, data)

	def verify_flash(self, data, address=None):
		"""Verifies the device's application area against a reference data set.

		Args:
			data    -- Data to verify against.
			address -- Address to verify from (or start of flash if `None`).
		"""

		if address is None:
			address = ATSAMD51.FLASH_APP_ADDRESS

		return self.flash_controllers[0].verify_flash(self.samba, address, data)

	def read_flash(self, address=None, length=None):
		"""Reads the device's application area.

		Args:
			address -- Address to read from (or start of flash if `None`).
			length  -- Length of the data to extract (or until end of flash if `None`).

		Returns:
			Byte array of the extracted data.
		"""

		if address is None:
			address = ATSAMD51.FLASH_APP_ADDRESS

		return self.flash_controllers[0].read_flash(self.samba, address, length)
