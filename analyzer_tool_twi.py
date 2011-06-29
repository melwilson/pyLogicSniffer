# -*- coding: UTF-8 -*-
'''TWI (aka I²C) analysis tool for pyLogicSniffer.
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
import itertools
import analyzer_tools

tool_menu_string = '&TWI'	# recommended menu string
tool_title_string = 'TWI'	# recommended title string


class AnalyzerDialog (wx.Dialog):
	'''Edit settings for TWI tool.'''
	def __init__ (self, parent, settings=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'TWI Settings')
		
		self.data_ctrl = wx.TextCtrl (self, wx.ID_ANY, '', validator=SpiPinValidator())
		self.clock_ctrl = wx.TextCtrl (self, wx.ID_ANY, '', validator=SpiPinValidator())
		
		if settings is not None:
			self.SetValue (settings)
			
		ts = wx.BoxSizer (wx.VERTICAL)
		gs = wx.FlexGridSizer (7, 2)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'SDA'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.data_ctrl, 1, 0)
		gs.Add (wx.StaticText (self, wx.ID_ANY, 'SCL'), 0, wx.ALIGN_CENTER_VERTICAL)
		gs.Add (self.clock_ctrl, 1, 0)
		ts.Add (gs, 1, wx.EXPAND|wx.ALL, 10)
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetSizer (ts)
		self.SetInitialSize()
			
	def SetValue (self, settings):
		if 'sda' in settings:	self.data_ctrl.SetValue (str (settings['sda']))
		if 'scl' in settings:	self.clock_ctrl.SetValue (str (settings['scl']))
		
	def GetValue (self):
		return {
			'sda': int (self.data_ctrl.GetValue()),
			'scl': int (self.clock_ctrl.GetValue()),
			}
			
			
class SpiPinValidator (analyzer_tools.SimpleValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= 31, 'Pin number must be an integer from 0 to 31.')
	
	
#===========================================================	
class AnalyzerPanel (wx.ScrolledWindow):
	'''Display TWI tool analysis.'''
	spi_settings = None
	def __init__ (self, parent, settings, tracedata):
		wx.ScrolledWindow.__init__ (self, parent, wx.ID_ANY)
		self.settings = settings
		self.tracedata = tracedata
		
		dg = self.display_grid = wx.grid.Grid (self, -1)
		dg.CreateGrid (0, 4)
		dg.SetRowLabelSize (0)
		dg.SetColLabelValue (0, '#')
		dg.SetColLabelValue (1, 'μSeconds')
		dg.SetColLabelValue (2, 'Status')
		dg.SetColLabelValue (3, 'Data')
		dg.SetColFormatNumber (0)
		dg.SetColFormatFloat (1)
		
		self.Analyze()
		dg.AutoSize()
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (dg, 1, wx.EXPAND)
		self.SetSizer (ts)
		self.SetInitialSize()
		
	def Analyze (self):
		settings = self.settings
		channel_data = self.tracedata.channel_data
		twi_bitstream = itertools.izip (
			itertools.count(),
			channel_data (settings['scl']), 
			channel_data (settings['sda'])
			)
		stime, old_scl, old_sda = twi_bitstream.next()
		data = 0
		bitcount = 0
		byte_count = 0
		for stime, scl, sda in twi_bitstream:
			if scl == old_scl and sda == old_sda:	# nothing happens
				continue

			if old_scl == scl == 1 and old_sda > sda:	# START condition
				self._log_start (stime)
				bitcount = byte_count = data = 0
			elif old_scl == scl == 1 and old_sda < sda:	# STOP condition
				if bitcount:	# data bits have been left hanging
					c = analyzer_tools.partial_bits (bitcount, data)
				else:
					c = ''
				self._log_stop (stime, c)
				bitcount = byte_count = data = 0
				
			elif old_scl == scl == 0:
				pass	# data line can change while clock is low
				
			elif sda == old_sda and old_scl < scl:	# data bit
				data = (data << 1) | sda
				bitcount += 1
				if bitcount == 8:	# complete character
					if byte_count == 0:
						self._log_addr_byte (stime, data)
					else:
						self._log_data_byte (stime, data, bitcount)
					byte_count += 1
				elif bitcount == 9:	# ACK/NAK following character
					if sda:
						self._log_nak (stime)
					else:
						self._log_ack (stime)
					data = bitcount = 0
			elif sda == old_sda and old_scl > scl:	# falling databyte clock (between bits)
				pass
				
			else:	# none of the above
				self._log_glitch (stime)
				
			old_scl, old_sda = scl, sda
			
		# finished examining the trace data ..	
		if bitcount > 0:	# sample ended with data transfer hanging
			dg, r = self._new_row()
			self._log_header (dg, r, stime)
			dg.SetCellValue (r, 2, 'End')
			if bitcount > 0:
				dg.SetCellValue (r, 3, analyzer_tools.partial_bits (bitcount, data))
			
	def _log_header (self, dg, r, sample):
		dg.SetCellValue (r, 0, str (sample))
		dg.SetCellValue (r, 1, str (self._sample_time (sample)*1e6))
		
	def _new_header (self, sample):
		dg = self.display_grid
		r = dg.GetNumberRows()
		dg.AppendRows (1)
		dg.SetCellValue (r, 0, str (sample))
		dg.SetCellValue (r, 1, str (self._sample_time (sample)*1e6))
		return dg, r
		
	def _new_row (self):
		dg = self.display_grid
		r = dg.GetNumberRows()
		dg.AppendRows (1)
		return dg, r
			
	def _log_ack (self, sample):
		dg, r = self._new_row()
		self._log_header (dg, r, sample)
		dg.SetCellValue (r, 2, 'ACK')
			
	def _log_addr_byte (self, sample, data):
		dg, r = self._new_header (sample)
		dg.SetCellValue (r, 2, 'Addr')
		dg.SetCellValue (r, 3, '0x%2x  %s' % (data>>1, 'WR'[data & 1],))
			
	def _log_data_byte (self, sample, data, bitcount):
		dg, r = self._new_header (sample)
		dg.SetCellValue (r, 3, '0x%2x' % (data,))
			
	def _log_glitch (self, sample):
		dg, r = self._new_header (sample)
		dg.SetCellValue (r, 2, 'Glitch')
			
	def _log_nak (self, sample):
		dg, r = self._new_header (sample)
		dg.SetCellValue (r, 2, 'NAK')
			
	def _log_start (self, sample):
		dg, r = self._new_header (sample)
		dg.SetCellValue (r, 2, 'Start')
			
	def _log_stop (self, sample, databyte):
		dg, r = self._new_header (sample)
		dg.SetCellValue (r, 2, 'Stop')
		dg.SetCellValue (r, 3, databyte)
		
	def _sample_time (self, sample):
		d = self.tracedata
		return float (sample - d.read_count + d.delay_count) / d.frequency
	
	
#===========================================================	
class AnalyzerFrame (analyzer_tools.AnalyzerFrame):
	'''Free-standing window to display SPI analyzer panel.'''
	
	def CreatePanel (self, settings, tracedata):
		'''Return an instance of the analysis panel to include in this window.'''
		return AnalyzerPanel (self, settings, tracedata)
		
	def SettingsDescription (self, settings):
		'''Return a string describing specific settings.'''
		return 'SDA:%(sda)d\tSCL:%(scl)d' % settings
		
	def SetTitle (self, title):
		'''Set the title for this window.'''
		analyzer_tools.AnalyzerFrame.SetTitle (self, '%s - %s' % (title, tool_title_string))
		
		
#===========================================================	
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
	