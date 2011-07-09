# -*- coding: UTF-8 -*-
'''Save and restore samples for pyLogicSniffer.
Copyright © 2011, Mel Wilson mwilson@melwilsonsoftware.ca

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

from logic_sniffer_classes import TraceData
import cPickle
import time

# possible alternative to cPickle is numpy.savetxt, ..loadtxt

def to_file (path, sample):
	with open (path, 'wb') as savefile:
		savefile.write ('#Sump analyzer sample\n')
		savefile.write ('#Saved on %s\n' % (time.asctime(),))
		cPickle.dump (sample, savefile, 0)
	
def from_file (path):
	with open (path, 'rb') as savefile:
		line = savefile.readline()
		print line,
		line = savefile.readline()
		print line,
		o = cPickle.load (savefile)
		return o
		
		
def to_csv (path, capture):
	'''Save SUMP capture data to a CSV file.'''
	import csv
	with open (path, 'wt') as savefile:
		writer = csv.writer (savefile)
		writer.writerow (['SUMP saved', time.ctime()])
		writer.writerow (['capture_time', time.ctime (capture.capture_time)])
		writer.writerow (['frequency', capture.frequency])
		writer.writerow (['read_count', capture.read_count])
		writer.writerow (['delay_count', capture.delay_count])
		writer.writerow (['channel_mask', capture.channel_mask])
		def channel_set (channel_mask=capture.channel_mask):
			for mask_bit, lo, hi in ((1,0,8), (2,8,16), (4,16,24), (8,24,32)):
				if not (channel_mask & mask_bit):	# channel masks exclude channels
					for x in xrange (lo, hi):
						yield x
		legends = capture.legend
		writer.writerow (['Legends'] + [legends.get (x, '') for x in channel_set()])
		writer.writerow (['Channels'] + list (channel_set()))
		data = capture.data
		for i in xrange (capture.read_count):
			def cbit (channel, di=data[i]):
				return (di >> channel) & 1
			writer.writerow ([i] + [cbit (c) for c in channel_set()])
	
def from_csv (path):
	raise NotImplementedError
	#~ import csv
	#~ reader = csv.reader (open (path, 'rt'))
	#~ r = reader.next()
	#~ if r[0] != 'SUMP trace':
		#~ raise ValueError
	

def to_text_file (path, sample):
	import numpy as np
	with open (path, 'wb') as savefile:
		savefile.write ('#Sump analyzer text sample\n')
		savefile.write ('#Saved on %s\n' % (time.asctime(),))
		savefile.write ('data\n')
		np.savetxt (savefile, sample.data)
	
def from_text_file (savefile):
	import numpy as np
	values = {}
	for line in savefile:
		h, t = line.strip().split ('=', 1)
		if h in ('frequency', 'read_count', 'delay_count', 'channel_mask'):
			values[h] = int (t, 0)
		elif h == 'data':
			values[h] = np.loadtxt (savefile, np.uint32)
			break
	return TraceData (**values)
