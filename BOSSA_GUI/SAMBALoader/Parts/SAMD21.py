#
#      Open Source SAM-BA Programmer
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from . import Part
from . import CortexM0p
from ..FlashControllers import NVMCTRL

class ATSAMD21(CortexM0p):
	"""Part class for all SAMD21 based parts.
	   Note: this will also return true for SAMR21 devices. TODO: fix this.
	"""

	def __init__(self, samba):
		"""Initializes class
		"""
		CortexM0p.__init__(self, samba)
		self.FLASH_CONTROLLER = (
			NVMCTRL(0x41004000)
			)

	@staticmethod
	def identify(ids):
		"""Determines if the given chip identifiers positively identify a SAMD21
		   series device.

		Args:
			id_name   -- Name of the chip identifier being tested.
			id_values -- Chip identifier values extracted from the part.

		Returns:
			`True` if the given identifiers suggest the part is a SAMD21
			series device.
		"""
		
		result = False
		try:
			id_values = ids['DSU']
			result = id_values.processor == 1 and id_values.family == 0 and id_values.series == 1
		except:
			return False
		return result

	def reset(self):
		"""Reset the chip
		"""

		self.samba.write_word(0xE000ED0C, 0x05FA0004) # This is the way bossa does it
