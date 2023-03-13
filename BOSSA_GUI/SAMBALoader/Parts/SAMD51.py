#
#      Open Source SAM-BA Programmer
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from . import Part
from . import CortexM3_4


class ATSAMD51(CortexM3_4):
	"""Part class for all SAMD51 based parts.
	"""

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
