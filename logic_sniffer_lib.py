# -*- coding: UTF-8 -*-
'''Functions and Data structures for pyLogicSniffer.
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

freq_units_text = ['GHz', 'MHz', 'KHz', 'Hz']
time_units_text = ['nS', u'μS', 'mS', 'S']
time_units_values = [1000000000, 1000000, 1000, 1]
	
def frequency_with_units (freq):
	'''Return a string with a frequency, scaled with convenient units.'''
	freq = float (freq)
	for u, d in zip (freq_units_text, time_units_values):
		fd = freq / d
		if fd > 1:
			return '%g %s' % (fd, u)
	return '%g' % (freq,)

def time_with_units (t):
	'''Return a string with time or duration scaled reasonably.'''
	t = float (t)
	for unit, d in zip (time_units_text, time_units_values):
		td = t * d
		if abs (td) < 1000:
			return '%g%s' % (td, unit)
	return '%g' % (t,)

class TraceData (object):
	'''Hold results of a capture.'''
	def __init__ (self, frequency, read_count, delay_count, channel_mask, data, legends=None, capture_time=None):
		self.frequency = frequency
		self.read_count = read_count
		self.delay_count = delay_count
		self.channel_mask = channel_mask
		if legends is None:
			legends = {}
		self.legends = legends	# dictionary relating channel numbers to display-labels
		if capture_time is None:
			capture_time = time.time()
		self.capture_time = capture_time
		self.data = data		# data values from SUMP device
		
	def channel_data (self, channel):
		'''Return a numpy array of samples for a single channel.'''
		return (self.data & (1 << channel)) != 0
		
	def channel_set (self):
		'''Yield the channel numbers allowed by the channel mask.'''
		channel_mask = self.channel_mask
		for (mask_bit, lo, hi) in ((1,0,8), (2,8,16), (4,16,24), (8,24,32)):
			if not (channel_mask & mask_bit):	# channel_mask bits disable channels
				for c in xrange (lo, hi):
					yield c
