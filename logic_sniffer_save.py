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

def to_file (path, sample):
	with open (path, 'wb') as savefile:
		savefile.write ('#Sump analyzer sample\n')
		savefile.write ('#Saved at %s\n' % (time.asctime(),))
		cPickle.dump (sample, savefile, 0)
	

def from_file_data (savefile):
	values = {}
	for line in savefile:
		h, t = line.strip().split ('=', 1)
		if h in ('frequency', 'read_count', 'delay_count', 'channel_mask'):
			values[h] = int (t, 0)
		elif h == 'data':
			if t.startswith ('array([') and t.endswith ('], dtype=uint32)'):
				values[h] = [int (x, 0) for x in t[8:-16].split (',')]
			else:
				raise ValueError
	return TraceData (**values)
	
def from_file (path):
	with open (path, 'rb') as savefile:
		line = savefile.readline()
		print line,
		line = savefile.readline()
		print line,
		o = cPickle.load (savefile)
		return o
		