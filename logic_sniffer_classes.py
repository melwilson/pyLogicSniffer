# -*- coding: ASCII -*-
'''Data structures for pyLogicSniffer.
Copyright 2011, Mel Wilson mwilson@melwilsonsoftware.ca

This file is part of pyLogicSniffer.

    pyLogicSniffer is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pyLogicSniffer is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with pyLogicSniffer.  If not, see <http://www.gnu.org/licenses/>.
'''

import time

class TraceData (object):
	'''Hold results of a capture.'''
	def __init__ (self, frequency, read_count, delay_count, channel_mask, data, legend=None, capture_time=None):
		self.frequency = frequency
		self.read_count = read_count
		self.delay_count = delay_count
		self.channel_mask = channel_mask
		if legend is None:
			legend = {}
		self.legend = legend	# dictionary relating channel numbers to display-labels
		if capture_time is None:
			capture_time = time.time()
		self.capture_time = capture_time
		self.data = data		# data values from SUMP device
		
	def channel_data (self, channel):
		'''Return samples for a single channel.'''
		return (self.data & (1 << channel)) != 0
