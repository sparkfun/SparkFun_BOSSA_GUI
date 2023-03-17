#
#      Open Source SAM-BA Programmer
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from . import FlashController
import logging


class NVMCTRL_D5x(FlashController.FlashControllerBase):
	CTRLA_OFFSET     = 0x0000
	CTRLB_OFFSET     = 0x0004
	PARAM_OFFSET     = 0x0008
	STATUS_OFFSET    = 0x0012
	INTFLAG_OFFSET   = 0x0010
	ADDRESS_OFFSET   = 0x0014

	CTRLA_CACHEDIS   = (3 << 14)
	CTRLA_SUSPEN_AUTOWS_MASK = 0xFFCF

	STATUSFLAG_READY = (1 << 0)

	CTRLB_CMD        = {
		'EP'  : 0x00,
		'EB'  : 0x01,
		'WP'  : 0x03,
		'PBC' : 0x15,
	}

	PAGES_PER_ROW    = 16


	def __init__(self, base_address):
		"""Initializes a NVMCTRL controller instance.

		Args:
			base_address -- Absolute base address of the NVMCTRL module
		"""

		self.base_address = base_address


	def _get_nvm_params(self, samba):
		"""Retrieves the NVM parameters and caches then in the class instance.

		Args:
			samba -- Core `SAMBA` instance bound to the device.
		"""

		nvm_param = samba.read_word(self.base_address + self.PARAM_OFFSET)

		# Bits 18:16 – PSZ[2:0] Page Size
		# Indicates the page size. Not all devices of the device families will provide all the page sizes indicated in the table.
		# Value Name Description
		# 0x0 8 8 bytes
		# 0x1 16 16 bytes
		# 0x2 32 32 bytes
		# 0x3 64 64 bytes
		# 0x4 128 128 bytes
		# 0x5 256 256 bytes
		# 0x6 512 512 bytes
		# 0x7 1024 1024 bytes
		self.page_size = 8 << ((nvm_param >> 16) & 0x07)

		# Bits 15:0 – NVMP[15:0] NVM Pages
		# Indicates the number of pages in the NVM main address space
		self.pages     = nvm_param & 0xFFFF


	def _wait_while_busy(self, samba):
		"""Waits until the NVM controller is ready for a new operation.

		Args:
			samba -- Core `SAMBA` instance bound to the device.
		"""
		while not samba.read_half_word(self.base_address + self.STATUS_OFFSET) & self.STATUSFLAG_READY:
			pass


	def _command(self, samba, command):
		"""Issues a low-level command to the NVMCTRL module.

		Args:
			samba   -- Core `SAMBA` instance bound to the device.
			command -- Command value to issue (see `CTRLB_CMD`)
		"""

		self._wait_while_busy(samba)

		reg  = (0xA5 << 8) | command
		samba.write_half_word(self.base_address + self.CTRLB_OFFSET, reg)


	def get_info(self):
		"""Read special registers.

		Returns:
			flash controller info as text.
		"""
		ret = ''
		return ret


	def erase_flash(self, samba, start_address, end_address=None):
		"""Erases the device's application area in the specified region.

		Args:
			samba         -- Core `SAMBA` instance bound to the device.
			start_address -- Start address to erase.
			end_address   -- End address to erase (or end of application area if `None`).
		"""

		self._get_nvm_params(samba)

		if end_address is None:
			end_address = self.pages * self.page_size

		start_address -= start_address % (self.PAGES_PER_ROW * self.page_size)
		end_address   -= end_address   % (self.PAGES_PER_ROW * self.page_size)

		logging.info('Erase Flash: 0x{0:X}..{1:X}'.format(start_address, end_address))

		for offset in range(start_address, end_address, self.PAGES_PER_ROW * self.page_size):
			samba.write_word(self.base_address + self.ADDRESS_OFFSET, offset >> 1)

			self._command(samba, self.CTRLB_CMD['EB'])
			self._wait_while_busy(samba)

		return True


	def program_flash(self, samba, address, data):
		"""Program's the device's application area.

		Args:
			samba   -- Core `SAMBA` instance bound to the device.
			address -- Address to program from.
			data    -- Data to program into the device.
		"""

		self._get_nvm_params(samba)

		# bossac does a read-modify-write, setting 7 and 18 to disable cache and configure manual page write
		ctrla = samba.read_half_word(self.base_address + self.CTRLA_OFFSET)
		ctrla |= self.CTRLA_CACHEDIS
		ctrla &= self.CTRLA_SUSPEN_AUTOWS_MASK
		samba.write_half_word(self.base_address + self.CTRLA_OFFSET, ctrla)

		self._command(samba, self.CTRLB_CMD['PBC'])
		self._wait_while_busy(samba)

		logging.info('Program Flash: Start 0x{0:X} Length 0x{1:X}'.format(address, len(data)))

		for (chunk_address, chunk_data) in self._chunk(self.page_size, address, data):
			for offset in range(0, len(chunk_data), 4):
				word = sum([x << (8 * i) for i, x in enumerate(chunk_data[offset : offset + 4])])
				samba.write_word(chunk_address + offset, word)

			self._command(samba, self.CTRLB_CMD['WP'])
			self._wait_while_busy(samba)
		return True


	def verify_flash(self, samba, address, data):
		"""Verifies the device's application area against a reference data set.

		Args:
			samba   -- Core `SAMBA` instance bound to the device.
			address -- Address to verify from.
			data    -- Data to verify against.

		Returns:
			`None` if the given data matches the data in the device at the
			specified offset, or a `(address, actual_word, expected_word)`
			tuple of the first mismatch.
		"""

		self._get_nvm_params(samba)

		logging.info('Verify Flash: Start 0x{0:X} Length 0x{1:X}'.format(address, len(data)))

		# From bossac:
		# "The SAM firmware has a bug reading powers of 2 over 32 bytes via USB."
		# So do the read in chunks of 32 bytes
		for (chunk_address, chunk_data) in self._chunk(32, address, data):
			actual_data = samba.read_block(chunk_address, len(chunk_data))

			for offset in range(0, len(chunk_data), 4):
				expected_word = sum([x << (8 * i) for i, x in enumerate(chunk_data[offset : offset + 4])])
				actual_word   = sum([x << (8 * i) for i, x in enumerate(actual_data[offset : offset + 4])])

				if actual_word != expected_word:
					return (chunk_address + offset, actual_word, expected_word)

		return None


	def read_flash(self, samba, address, length=None):
		"""Reads the device's application area.

		Args:
			samba   -- Core `SAMBA` instance bound to the device.
			address -- Address to read from.
			length  -- Length of the data to extract (or until end of application area if `None`).

		Returns:
			Byte array of the extracted data.
		"""

		self._get_nvm_params(samba)

		if length is None:
			length = (self.pages * self.page_size) - address

		logging.info('Read Flash: Start 0x{0:X} Length 0x{1:X}'.format(address, length))

		if (length < 32):
			return samba.read_block(address, length)

		actual_data = bytearray(0)
		readBytes = 0

		while readBytes < (length - 32):
			actual_data += samba.read_block(address + readBytes, 32) # Read in chunks of 32
			readBytes += 32

		if (readBytes < length):
			actual_data += samba.read_block(address + readBytes, length - readBytes) # Read final chunk

		return actual_data
