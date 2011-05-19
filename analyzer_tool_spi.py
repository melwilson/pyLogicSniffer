# -*- coding: UTF-8 -*-
'''SPI analysis tool for pyLogicSniffer.
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
import itertools, time
from analyzer_tools import SimpleValidator

tool_menu_string = '&SPI'	# recommended menu string
tool_title_string = 'SPI'	# recommended title string

class AnalyzerDialog (wx.Dialog):
	'''Edit settings for SPI tool.'''
	def __init__ (self, parent, settings=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'SPI Settings')
		
		self.clock_ctrl = wx.TextCtrl (self, wx.ID_ANY, '', validator=SpiPinValidator())
		self.mosi_ctrl = wx.TextCtrl (self, wx.ID_ANY, '', validator=SpiPinValidator())
		self.miso_ctrl = wx.TextCtrl (self, wx.ID_ANY, '', validator=SpiPinValidator())
		self.ssel_ctrl = wx.TextCtrl (self, wx.ID_ANY, '', validator=SpiPinValidator())
		self.master_ctrl = wx.CheckBox(self, wx.ID_ANY, '')
		self.leading_ctrl = wx.RadioBox (self, -1, 'Leading Bit', choices=['MSB', 'LSB'])
		self.leading_ctrl.SetSelection (0)
		self.cpol_ctrl = wx.RadioBox (self, -1, 'Leading Edge', choices=['Rising', 'Falling'])
		self.cpol_ctrl.SetSelection (0)
		self.cpha_ctrl = wx.RadioBox (self, -1, 'Leading Edge Action', choices=['Sample', 'Setup'])
		self.cpha_ctrl.SetSelection (0)
		
		if settings is not None:
			self.SetValue (settings)
			
		gs = wx.FlexGridSizer (7, 2)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'SCK'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.clock_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'MOSI'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.mosi_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'MISO'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.miso_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, '/SS'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.ssel_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'Master'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.master_ctrl, 1, 0)
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (gs, 1, wx.ALIGN_CENTER)
		ts.Add (self.leading_ctrl, 0, wx.EXPAND)
		clock_box = wx.StaticBox (self, -1, 'Clock')	# in Python, StaticBoxSizer can't create this
		clock_box_sizer = wx.StaticBoxSizer (clock_box, wx.VERTICAL)
		clock_box_sizer.Add (self.cpol_ctrl, 0, wx.EXPAND)
		clock_box_sizer.Add (self.cpha_ctrl, 0, wx.EXPAND)
		ts.Add (clock_box_sizer, 0, wx.EXPAND)
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
			
	def SetValue (self, settings):
		self.clock_ctrl.SetValue (str (settings['sck']))
		self.mosi_ctrl.SetValue (str (settings['mosi']))
		self.miso_ctrl.SetValue (str (settings['miso']))
		self.ssel_ctrl.SetValue (str (settings['nss']))
		self.master_ctrl.SetValue (settings['master'])
		self.leading_ctrl.SetStringSelection (settings['leading'])
		self.cpol_ctrl.SetSelection (settings['mode'] >> 1)
		self.cpha_ctrl.SetSelection (settings['mode'] & 1)
		
	def GetValue (self):
		return {
			'sck': int (self.clock_ctrl.GetValue()),
			'mosi': int (self.mosi_ctrl.GetValue()),
			'miso': int (self.miso_ctrl.GetValue()),
			'nss': int (self.ssel_ctrl.GetValue()),
			'mode': (self.cpol_ctrl.GetSelection() << 1) | self.cpha_ctrl.GetSelection(),
			'master': self.master_ctrl.IsChecked(),
			'leading': self.leading_ctrl.GetStringSelection(),
			'cpol': self.cpol_ctrl.GetSelection(),		# optional
			'cpha': self.cpha_ctrl.GetSelection(),	# optional
			}
			
			
class SpiPinValidator (SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= 31, 'Pin number must be an integer from 0 to 31.')
	
	
#===========================================================	
class AnalyzerPanel (wx.ScrolledWindow):
	'''Display SPI tool analysis.'''
	spi_settings = None
	def __init__ (self, parent, settings, tracedata):
		wx.ScrolledWindow.__init__ (self, parent, wx.ID_ANY)
		self.settings = settings
		self.tracedata = tracedata
		
		dg = self.display_grid = wx.grid.Grid (self, -1)
		dg.CreateGrid (0, 5)
		dg.SetRowLabelSize (0)
		dg.SetColLabelValue (0, '#')
		dg.SetColLabelValue (1, 'μSeconds')
		dg.SetColLabelValue (2, 'Status')
		dg.SetColLabelValue (3, 'MOSI')
		dg.SetColLabelValue (4, 'MISO')
		dg.SetColFormatNumber (0)
		dg.SetColFormatFloat (1)
		
		self.Analyze()
		dg.AutoSize()
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (dg, 1, wx.EXPAND)
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		
	def Analyze (self):
		settings = self.settings
		pol = (settings['mode'] >> 1) & 1	# clock polarity
		pha = settings['mode'] & 1			# sample/setup phase
		trace_data = self.tracedata.data
		spi_data = itertools.izip (
			itertools.count(),
			trace_data & (1<<settings['nss']), 
			trace_data & (1<<settings['sck']), 
			trace_data & (1<<settings['miso']),
			trace_data & (1<<settings['mosi'])
			)
		stime, oldnss, oldsck, oldmiso, oldmosi = spi_data.next()
		mosi_data = miso_data = 0
		miso_bitcount = mosi_bitcount = 0
		for stime, nss, sck, miso, mosi in spi_data:
			if oldnss > nss:	# SPI just became active
				self._log_nss_enable (stime)
				mosi_data = miso_data = 0
				miso_bitcount = mosi_bitcount = 0
			elif oldnss < nss:	# SPI just became inactive
				self._log_nss_disable (stime, mosi_bitcount, mosi_data, miso_bitcount,miso_data)
			if not nss:	# SPI is active
				if oldsck^pol < sck^pol :	# leading clock edge
					if pha:	# setup output level
						mosi_data = (mosi_data << 1) | bool (mosi)
						mosi_bitcount += 1
					else:	# sample input level
						miso_data = (miso_data << 1) | bool (miso)
						miso_bitcount += 1
				elif oldsck^pol > sck^pol:	# trailing clock edge
					if pha:	# sample input level
						miso_data = (miso_data << 1) | bool (miso)
						miso_bitcount += 1
					else:	# setup output level
						mosi_data = (mosi_data << 1) | bool (mosi)
						mosi_bitcount += 1
				if miso_bitcount > 7:
					self._log_data_byte (stime, None, miso_data)
					miso_data = 0
					miso_bitcount = 0
				if mosi_bitcount > 7:
					self._log_data_byte (stime, mosi_data, None)
					mosi_data = 0
					mosi_bitcount = 0
				
			oldnss, oldsck, oldmiso, oldmosi = nss, sck, miso, mosi
			
		# finished examining the trace data ..	
		if miso_bitcount > 0 or mosi_bitcount > 0:
			dg, r = self._new_row()
			self._log_header (dg, r, stime)
			dg.SetCellValue (r, 2, 'End')
			if mosi_bitcount > 0:
				dg.SetCellValue (r, 3, partial_bits (mosi_bitcount, mosi_data))
			if miso_bitcount > 0:
				dg.SetCellValue (r, 4, partial_bits (miso_bitcount, miso_data))
			
	def _log_header (self, dg, r, sample):
		dg.SetCellValue (r, 0, str (sample))
		dg.SetCellValue (r, 1, str (self._sample_time (sample)*1e6))
		
	def _new_row (self):
		dg = self.display_grid
		r = dg.GetNumberRows()
		dg.AppendRows (1)
		return dg, r
			
	def _log_nss_disable (self, sample, mosi_bitcount, mosi_data, miso_bitcount, miso_data):
		dg, r = self._new_row ()
		self._log_header (dg, r, sample)
		dg.SetCellValue (r, 2, 'Disable')
		if mosi_bitcount > 0:
			dg.SetCellValue (r, 3, partial_bits (mosi_bitcount, mosi_data))
		if miso_bitcount > 0:
			dg.SetCellValue (r, 4, partial_bits (miso_bitcount, miso_data))
			
	def _log_nss_enable (self, sample):
		dg, r = self._new_row ()
		self._log_header (dg, r, sample)
		dg.SetCellValue (r, 2, 'Enable')
		
	def _log_data_byte (self, sample, mosi, miso):
		dg, r = self._new_row ()
		self._log_header (dg, r, sample)
		if mosi is not None:
			dg.SetCellValue (r, 3, hex (mosi))
		if miso is not None:
			dg.SetCellValue (r, 4, hex (miso))
		
	def _sample_time (self, sample):
		d = self.tracedata
		return float (sample - d.read_count + d.delay_count) / d.frequency
	
	
#===========================================================	
class AnalyzerFrame (wx.Dialog):
	'''SPI tool analysis in an independent Window.'''
	def __init__ (self, parent, settings, tracedata, title='Data'):
		wx.Dialog.__init__ (self, parent, -1, ''
				, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX)
		self.SetTitle (title)
		self.settings = settings
		self.panel = AnalyzerPanel (self, settings, tracedata)
		self.Bind (wx.EVT_CLOSE, self.OnClose)
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (wx.StaticText (self, -1, time.ctime (tracedata.capture_time)), 0, wx.EXPAND)
		ts.Add (wx.StaticText (self, -1, 'SCK:%(sck)d\tMOSI:%(mosi)d\tMISO:%(miso)d\tnSS:%(nss)d' % settings), 0, wx.EXPAND)
		ts.Add (self.panel, 1, wx.EXPAND)
		button = wx.Button (self, -1, 'Done')
		button.Bind (wx.EVT_BUTTON, self.OnClose)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add ((1,1), 1)
		hs.Add (button, 0, wx.ALIGN_RIGHT)
		ts.Add (hs, 0, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
			
	def OnClose (self, evt):
		wx.CallAfter (self.GetParent().RemoveToolWindow,  self)
		self.Destroy()
		
	def SetTitle (self, title):
		wx.Dialog.SetTitle (self, title + ' - SPI')
		
		
#===========================================================	
def partial_bits (bitcount, data, msbfirst=True):
	'''String representing a byte of less than 8 bits, MSB first.'''
	s = [str ((data >> i) & 1) for i in xrange (bitcount)]
	if msbfirst:
		return ''.join (s[::-1]) + 'x'*(8-bitcount)
	else:
		return 'x'*(8-bitcount) + ''.join(s)

		
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
		'''Application.'''
		def OnInit (self):
			frame = MyTestFrame ('AnalyzerDialog Test', 'About '+__file__, __doc__)
			frame.Show (True)
			self.SetTopWindow (frame)
			return True

	app = MyApp (0)
	app.MainLoop()
	