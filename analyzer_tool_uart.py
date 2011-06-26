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
import analyzer_tools

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
baud_values = [
	110, 300, 600, 1200, 2400, 4800, 9600,
	14400, 19200, 28800, 
	31250, # MIDI
	33600, 38400, 56000, 57600,
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
	#~ print 'optional_int:', repr (s)
	if base is not None:
		return int (s, base)
	else:
		return int (s)
		
parity_settings = {
	'None':0, 'Even':1, 'Odd':2,
	'n':0, 'e':1, 'o':2,
	0:'None', 1:'Even', 2:'Odd',
	}


def nearest_baud (estimate):
	'''Find the official baud rate closest to an estimate.'''
	baud, diff = baud_values[0], abs (estimate-baud_values[0])
	for b in baud_values[1:]:
		d = abs (estimate-b)
		if d < diff:
			baud, diff = b, d
	return baud

def baud_difference (estimate, official=None):
	'''Return string describing the difference between estimated and official baud.'''
	if official is None:
		official = nearest_baud (estimate)
	if official == estimate:
		return ''
	elif estimate > official:
		return '(%s + %s%%)' % (official, int ((estimate-official)/float (official) * 100))
	else:
		return '(%s - %s%%)' % (official, int ((official-estimate)/float (official) * 100))
	
def expand_template (bitwidth, defs):
	'''Turn Run-Length-Encoded list into bits.'''
	return np.array (sum (([bit]*(count*bitwidth) for count, bit in defs), []), np.int8)
		
def character_template (parity, length, stop):
	'''Mask/value pair, and data length for matching a character format against a sample slice.'''
	# Significant fields are Start-bit, parity (if any), Stop-bit
	mask_template = tuple ( ((n,v) for n, v in ((1,1), (length,0), (parity!=0, 1), (stop,1)) if n > 0) )
	# Set expected values for Start and Stop bits, initialize parity field (if any)
	value_template = tuple ( ((n,v) for n, v in ((1,0), (length,0), (parity!=0, parity==2), (stop,1)) if n > 0) )
	return mask_template, value_template
	
def character_template_set ():
	templates = {}
	for test_parity in xrange (0, 2+1):
		for test_length in xrange (5, 8+1):
			for test_stop in xrange (1, 2+1):
				k = (test_parity, test_length, test_stop)
				templates[k] = character_template (*k)
	return templates
	
character_templates = character_template_set()	# for bitstream analysis later
	
score_signs = [0, 0]
def character_score (samples, mask, val, (parity, length, stops), bitwidth):
	'''Score a sample slice for its match with a template.'''
	if parity:
		val = np.array (val)
		parx = (length+1)*bitwidth
		for i in xrange (bitwidth, (length+1)*bitwidth, bitwidth):
			val[parx: parx+bitwidth] ^= samples[i: i+bitwidth]
	matches = (samples == val) * 2 - 1	# array of -1..1 for no-match..match
	result = sum (matches * mask)		# score only significant sample bits
	score_signs [result >= 0] += 1
	return result

#===========================================================
class AnalyzerDialog (wx.Dialog):
	'''Edit settings for UART tool.'''
	def __init__ (self, parent, settings=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, tool_title_string+' Settings')
		
		self.pin_ctrl = wx.TextCtrl (self, wx.ID_ANY, '0', validator=PinValidator())
		self.auto_ctrl = wx.CheckBox(self, wx.ID_ANY, '')
		self.baud_ctrl = wx.ComboBox(self, wx.ID_ANY, '9600'
			, choices=[str(x) for x in baud_values]
			, validator=BaudValidator())
		self.parity_ctrl = wx.RadioBox (self, wx.ID_ANY, choices=['None', 'Even', 'Odd'])
		self.length_ctrl = wx.ComboBox (self, wx.ID_ANY, '8'
			, choices=['5', '6', '7', '8', '9']
			, validator=LengthValidator())
		self.stop_ctrl = wx.RadioBox (self, wx.ID_ANY, '', choices=['1', '2'])
		
		gs = wx.FlexGridSizer (6, 2)
		def add_labeled_ctrl (label, ctrl):
			'''Add a control to gs with a preceding StaticText label.'''
			gs.Add (wx.StaticText (self, wx.ID_ANY, label), 0, wx.ALIGN_CENTER_VERTICAL)
			gs.Add (ctrl, 1, 0)
		
		add_labeled_ctrl ('Pin', self.pin_ctrl)
		add_labeled_ctrl ('Auto', self.auto_ctrl)
		add_labeled_ctrl ('Baud', self.baud_ctrl)
		add_labeled_ctrl ('Parity', self.parity_ctrl)
		add_labeled_ctrl ('Length', self.length_ctrl)
		add_labeled_ctrl ('Stop', self.stop_ctrl)
		
		if settings is not None:
			self.SetValue (settings)
			
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (gs, 1, wx.ALIGN_CENTER)
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetSizer (ts)
		self.SetInitialSize()
			
	def SetValue (self, settings):
		#~ print 'SetValue:', settings
		pin = settings.get ('pin', None)
		if pin is not None:	self.pin_ctrl.SetValue (str (pin))
		auto = settings.get ('auto', None)
		if auto is not None:	self.auto_ctrl.SetValue (int (auto))
		baud = settings.get ('baud', None)
		if baud is not None:	self.baud_ctrl.SetStringSelection (str (baud))
		parity = settings.get ('parity', None)
		if parity is not None:	self.parity_ctrl.SetStringSelection (parity_settings [parity])
		length = settings.get ('length', None)
		if length is not None:	self.length_ctrl.SetStringSelection (str (length))
		stop = settings.get ('stop', None)
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
			
class BaudValidator (analyzer_tools.SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= baud_values[-1], 'Baud rate must be an integer from 0 to 115200.')
			
class LengthValidator (analyzer_tools.SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 5 <= v <= 9, 'Character length must be an integer from 5 to 9.')
			
class PinValidator (analyzer_tools.SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= 31, 'Pin number must be an integer from 0 to 31.')
	
#===========================================================	
class AnalyzerPanel (wx.ScrolledWindow):
	'''Display UART analysis.'''
	def __init__ (self, parent, settings, tracedata):
		wx.ScrolledWindow.__init__ (self, parent, wx.ID_ANY)
		self.settings = settings
		#~ print 'AnalyzerPanel settings:', settings
		self.tracedata = tracedata
		channel = self.settings['pin']
		self.serial_data = (self.tracedata.data & (1<<channel)) != 0
		
		dg = self.display_grid = wx.grid.Grid (self, -1)
		dg.CreateGrid (0, 5)
		dg.SetRowLabelSize (0)
		dg.SetColLabelValue (0, '#')
		dg.SetColLabelValue (1, 'μSeconds')
		dg.SetColLabelValue (2, 'Status')
		dg.SetColLabelValue (3, 'hex')
		dg.SetColLabelValue (4, 'ASCII')
		dg.SetColFormatNumber (0)
		dg.SetColFormatFloat (1)
		
		self.Analyze()
		dg.AutoSize()
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (dg, 1, wx.EXPAND)
		self.SetSizer (ts)
		self.SetInitialSize()
		
	def Analyze (self):
		'''Construct a UART interpretation of the trace data.'''
		if self.settings['auto'] or True:
			self._auto_analyze_baud ()
			self._auto_analyze_format ()
			
		# Report contents of serial data ..
		data = self.serial_data
		offset = 0
		self.parity = 0
		self.character_length = 8
		self.stop_bits = 1
		samples_per_char = (1 + self.character_length + self.stop_bits) * (self.tracedata.frequency / self.settings['baud'])
		while offset < len (data):
			c = self._match_character (data[offset:], self.parity, self.character_length, self.stop_bits, offset)
			if c is not None:
				self._log_data_byte (offset, c)
				offset += samples_per_char
			else:
				offset += 1
				
		self.GetParent().Refresh()
		
	def _auto_analyze_baud (self):
		# Find most probable samples-per-bit value ..
		self._pulse_histogram()
		zeros = [(c, d) for (d, c) in self.hist[0].items()]
		zeros.sort()
		ones = [(c, d) for (d, c) in self.hist[1].items()]
		ones.sort()
		print 'Zeros (count, duration):', zeros[::-1]
		print 'Ones  (count, duration):', ones[::-1]
		print 'Clock:', self.tracedata.frequency, 'Hz'
		self.auto_bitsize = zeros[-1][1]
		self.auto_baud = self.tracedata.frequency / self.auto_bitsize
		print 'Baud: ', self.auto_baud
		print 'Harmonic zeros:', self._harmonic_histogram (zeros)[::-1]
		print 'Harmonic ones:', self._harmonic_histogram (ones)[::-1]
		self.settings['baud'] = self.auto_baud
		print 'Est.baud \t%s %s\n' % (self.auto_baud, baud_difference (self.auto_baud))
		
	def _auto_analyze_format (self):
		# Automatic format detection ..
		templates = character_template_set ()
		format_scores = dict ((k, 0) for k in templates)
		#~ data = self.serial_data
		data = np.array (self.serial_data, np.int16)
		data_length = len (data)
		for offset in xrange (1, data_length):
			if data[offset-1] == 1 and data[offset] == 0:	# possible start-bit here
				for k, (mask, val) in templates.items():
					bitmask = expand_template (self.auto_bitsize, mask)
					bitval = expand_template (self.auto_bitsize, val)
					width = len (bitmask)
					if offset+width < data_length:
						format_scores[k] += character_score (data[offset:offset+width], bitmask, bitval, k, self.auto_bitsize)
		print 'Score signs:', score_signs
		scores = [(v, k) for k, v in format_scores.items()]
		scores.sort()
		print 'Format scores:'
		for x in scores[::-1]:
			print x
		
	def _harmonic_histogram (self, ph):
		hist = collections.defaultdict (int)
		pulses = sorted (ph, cmp=lambda x, y: cmp(x[1], y[1]))	# sort by frequency
		harmonic = []
		while pulses:
			i, f = pulses[0]
			pulses = pulses[1:]
			harmonic.append ( (i + sum ([j for j, g in pulses if GCD (f, g) == f]), f) )
		harmonic.sort()
		return harmonic
		
	def _log_data_byte (self, sample, byte):
		dg, r = self._new_row ()
		self._log_header (dg, r, sample)
		dg.SetCellValue (r, 3, '0x%02x' % (byte,))
		dg.SetCellValue (r, 4, ASCII_ctl_chars.get (byte, chr (byte)))
			
	def _log_header (self, dg, r, sample):
		dg.SetCellValue (r, 0, str (sample))
		dg.SetCellValue (r, 1, str (self._sample_time (sample)*1e6))
		
	def _match_character (self, data, parity, length, stop, offset):
		w = self.tracedata.frequency / self.settings['baud']
		try:
			for b in data[:w-2]:
				if b != 0:
					return None	# invalid start bit
			plength = length + (parity!=0)
			for b in data[(1+plength)*w+2:(1+plength+stop)*w-2]:
				if b != 1:
					return None	# invalid stop bit
			bits = [data[bx] for bx in xrange (int ((w*3) / 2), plength*w, w)]
			v = 0
			for b in bits[::-1]:
				v = v * 2 + b
			return v
		except IndexError:
			return None

	def _new_row (self):
		dg = self.display_grid
		r = dg.GetNumberRows()
		dg.AppendRows (1)
		return dg, r
		
	def _pulse_histogram (self):
		'''dict giving Histograms of pulse durations in the sample.'''
		hist = [collections.defaultdict (int), collections.defaultdict (int)]
		samples = self.serial_data
		v, c = samples[0], 1
		for b in samples[1:]:
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
	
	
#===========================================================	
class AnalyzerFrame (analyzer_tools.AnalyzerFrame):
	'''Free-standing window to display UART analyzer panel.'''
	
	def CreatePanel (self, settings, tracedata):
		'''Return an instance of the analysis panel to include in this window.'''
		return AnalyzerPanel (self, settings, tracedata)
		
	def SettingsDescription (self, settings):
		'''Return a string describing specific settings.'''
		e = baud_difference (settings['baud'])
		d = '%s%s%s' % ('neo'[settings['parity']], settings['length'], settings['stop'])
		return 'Pin:%(pin)s\tBaud:%(baud)s ' % settings + e + '\t' + d
		
	def SetTitle (self, title):
		'''Set the title for this window.'''
		analyzer_tools.AnalyzerFrame.SetTitle (self, '%s - %s' % (title, tool_title_string))


def GCD (n1, n2):
	if n1 < n2:
		n1, n2 = n2, n1
	while n2:
		n1, n2 = n2, n1 % n2
	return n1
		
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
	