# -*- coding: UTF-8 -*-
'''UART analysis tool for pyLogicSniffer.
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

import wx
import numpy as np
import collections, itertools
from analyzer_tools import SimpleValidator

tool_menu_string = '&UART'	# recommended menu string
tool_title_string = 'UART'	# recommended title string

ASCII_ctl_chars = {
	0:'␀', 1:'␁', 2:'␂', 3:'␃', 4:'␄', 5:'␅', 6:'␆', 7:'␇',
	8:'␈', 9:'␉', 10:'␊', 11:'␋', 12:'␌', 13:'␍', 14:'␎', 15:'␏',
	16:'␐', 17:'␑', 18:'␒', 19:'␓', 20:'␔', 21:'␕', 22:'␖', 23:'␗',
	24:'␘', 25:'␙', 26:'␚', 27:'␛', 28:'␜', 29:'␝', 30:'␞', 31:'␟',
	32:'␠', 
	127:'␡',
	}
_baud_values = [
	110, 300, 600, 1200, 2400, 4800, 9600,
	14400, 19200, 28800, 31250, 33600, 38400, 56000, 57600,
	115200, 230400, 
	]
baudot_murray_letters = {
	0:'␀', 1:'T', 2:'␍', 3:'O', 4:'␠', 5:'H', 6:'N', 7:'M',
	8:'␊', 9:'L', 10:'R', 11:'G', 12:'I', 13:'P', 14:'C', 15:'V',
	16:'E', 17:'Z', 18:'D', 19:'B', 20:'S', 21:'Y', 22:'F', 23:'X',
	24:'A', 25:'W', 26:'J', 27:'⑨', 28:'U', 29:'Q', 30:'K', 31:'Ⓐ',
	}
baudot_murray_figures = {
	0:'␀', 1:'5', 2:'␍', 3:'9', 4:'␠', 5:'#', 6:',', 7:'.',
	8:'␊', 9:')', 10:'4', 11:'&', 12:'8', 13:'0', 14:':', 15:';',
	16:'3', 17:'"', 18:'$', 19:'?', 20:"'", 21:'6', 22:'!', 23:'/',
	24:'-', 25:'2', 26:'␇', 27:'⑨', 28:'7', 29:'1', 30:'(', 31:'Ⓐ',
	}
baudot_murray_shifts = {31:baudot_murray_letters, 27:baudot_murray_figures}

optional_int_settings = {
	None:None, 'None':None, '':None,
	'True':True, 'False':False,
	}
def optional_int (s, base=None):
	if s in optional_int_settings:
		return optional_int_settings [s]
	print 'optional_int:', repr (s)
	if base is not None:
		return int (s, base)
	else:
		return int (s)
		
parity_settings = {
	'None':0, 'Even':1, 'Odd':2,
	0:'None', 1:'Even', 2:'Odd',
	}

class AnalyzerDialog (wx.Dialog):
	'''Edit settings for UART tool.'''
	def __init__ (self, parent, settings=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, tool_title_string+' Settings')
		
		self.pin_ctrl = wx.TextCtrl (self, wx.ID_ANY, '0', validator=PinValidator())
		self.auto_ctrl = wx.CheckBox(self, wx.ID_ANY, '')
		self.baud_ctrl = wx.ComboBox(self, wx.ID_ANY, '9600'
			, choices=[str(x) for x in _baud_values]
			, validator=BaudValidator())
		self.parity_ctrl = wx.RadioBox (self, wx.ID_ANY, choices=['None', 'Even', 'Odd'])
		self.length_ctrl = wx.ComboBox (self, wx.ID_ANY, '8'
			, choices=['5', '6', '7', '8', '9']
			, validator=LengthValidator())
		self.stop_ctrl = wx.RadioBox (self, wx.ID_ANY, '', choices=['1', '2'])
		gs = wx.FlexGridSizer (6, 2)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Pin'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.pin_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Auto'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.auto_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Baud'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.baud_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Parity'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.parity_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Length'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.length_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Stop'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.stop_ctrl, 1, 0)
		
		if settings is not None:
			self.SetValue (settings)
			
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (gs, 1, wx.ALIGN_CENTER)
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
			
	def SetValue (self, settings):
		print 'SetValue:', settings
		pin = settings['pin']
		if pin is not None:	self.pin_ctrl.SetValue (str (pin))
		auto = settings['auto']
		if auto is not None:	self.auto_ctrl.SetValue (auto)
		baud = settings['baud']
		if baud is not None:	self.baud_ctrl.SetStringSelection (str (baud))
		parity = settings['parity']
		if parity is not None:	self.parity_ctrl.SetStringSelection (parity_settings [parity])
		length = settings['length']
		if length is not None:	self.length_ctrl.SetStringSelection (str (length))
		stop = settings['stop']
		if stop is not None:	self.stop_ctrl.SetStringSelection (str (stop))
		
	def GetValue (self):
		return {
			'pin': optional_int (self.pin_ctrl.GetValue()),
			'auto': optional_int (self.auto_ctrl.GetValue()),
			'baud': optional_int (self.baud_ctrl.GetStringSelection()),
			'parity': parity_settings [self.parity_ctrl.GetStringSelection()],
			'length': optional_int (self.length_ctrl.GetStringSelection()),
			'stop': optional_int (self.stop_ctrl.GetStringSelection()),
			}
			
class BaudValidator (SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= 115200, 'Baud rate must be an integer from 0 to 115200.')
			
class LengthValidator (SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 5 <= v <= 8, 'Pin number must be an integer from 5 to 8.')
			
class PinValidator (SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= 31, 'Pin number must be an integer from 0 to 31.')
	
#===========================================================	
class AnalyzerPanel (wx.ScrolledWindow):
	'''Display UART analysis.'''
	def __init__ (self, parent, settings, tracedata):
		wx.ScrolledWindow.__init__ (self, parent, wx.ID_ANY)
		self.settings = settings
		self.tracedata = tracedata
		
		self.Analyze()
		
	def Analyze (self):
		'''Construct a UART interpretation of the trace data.'''
		if self.settings['auto'] or True:
			self._pulse_histogram()
			zeros = [(c, d) for (d, c) in self.hist[0].items()]
			zeros.sort()
			ones = [(c, d) for (d, c) in self.hist[1].items()]
			ones.sort()
			print 'Zeros (count, duration):', zeros
			print 'Ones  (count, duration):', ones
			print 'Clock:', self.tracedata.frequency, 'Hz'
			self.auto_bitsize = zeros[-1][1]
			self.auto_baud = self.tracedata.frequency / self.auto_bitsize
			print 'Baud: ', self.auto_baud
		
		# Auto baud detect -- like fourier analysis
		# Auto protocol detect -- bits/byte, parity, stop bits
	
	def _channel_data (self):
		'''Inidvidual samples from the UART data channel.'''
		channel = self.settings['pin']
		mask = 1 << channel
		for v in self.tracedata.data:
			yield bool (v & mask)
		
	def _pulse_histogram (self):
		'''Histograms of pulse durations in the sample.'''
		hist = [collections.defaultdict (int), collections.defaultdict (int)]
		samples = self._channel_data()
		v, c = samples.next(), 1
		for b in samples:
			if b == v:
				c += 1
			else:
				hist[v][c] += 1	# account for the run that just ended
				v, c = b, 1
		hist[v][c] += 1	# account for the last run
		self.hist = hist
		
	def _sample_time (self, sample):
		'''The real-world time at which a sample was taken.'''
		settings = self.tracedata
		return float (sample - settings.read_count + settings.delay_count) / settings.frequency

def GCD (n1, n2):
	if n1 < n2:
		n1, n2 = n2, n1
	while n2:
		n1 -= n2
		if n1 < n2:	n1, n2 = n2, n1
	return n1
	
print
for i in xrange (12):
	print 12, i, GCD (i, 12)
print
		
# Test jig ...
if __name__ == '__main__':
	from simple_test_frame import SimpleTestFrame

	class MyTestFrame (SimpleTestFrame):
		dialog_data = None
		def OnTest (self, evt):
			dlg = AnalyzerDialog (self, self.dialog_data)
			if dlg.ShowModal () == wx.ID_OK:
				if not dlg.Validate():
					return
				self.dialog_data = dlg.GetValue()
			dlg.Destroy()
		
	class MyApp (wx.App):
		def OnInit (self):
			frame = MyTestFrame ('UART AnalyzerDialog Test', 'About '+__file__, __doc__)
			frame.Show (True)
			self.SetTopWindow (frame)
			return True

	app = MyApp (0)
	app.MainLoop()
	