# -*- coding: ASCII -*-
'''Maintain SUMP settings in config (.ini) files.
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
import ConfigParser as configparser
import sump

sump_int_parms = ['divider', 'read_count', 'delay_count', 'inverted',
		'external', 'filter', 'demux', 'channel_groups', 
		]
sump_str_parms = ['trigger_enable']
trigger_int_parms = ['trigger_mask', 'trigger_values',
		'trigger_delay', 'trigger_level', 'trigger_channel',
		'trigger_serial', 'trigger_start'
		]
	
def save_config (path, config):
	'''Save SUMP device settings to a config file.'''
	p = configparser.RawConfigParser()
	p.add_section ('sump')
	for parm in sump_int_parms:
		p.set ('sump', parm, int (getattr (config, parm)))
	for parm in sump_str_parms:
		p.set ('sump', parm, getattr (config, parm))
	for stage in xrange (4):
		section = 'stage%d' % (stage,)
		p.add_section (section)
		for parm in trigger_int_parms:
			p.set (section, parm, int (getattr (config, parm)[stage]))
	with open (path, 'wt') as fp:
		p.write (fp)
			
def load_config (path):
	'''Load SUMP device settings from a config file.'''
	p = configparser.RawConfigParser()
	p.read ([path])
	c = sump.SumpDeviceSettings()
	for parm in sump_int_parms:
		setattr (c, parm, p.getint ('sump', parm))
	for parm in sump_str_parms:
		setattr (c, parm, p.get ('sump', parm))
	for stage in xrange (4):
		section = 'stage%d' % (stage,)
		for parm in trigger_int_parms:
			attr = getattr (c, parm)
			attr[stage] = p.getint (section, parm)
	return c
