# -*- coding: UTF-8 -*-
'''Edit trace legends for pyLogicSniffer.
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
import time
from logic_sniffer_lib import frequency_with_units


class SimpleValidator (wx.PyValidator):
	'''Validators with simple, sensible defaults.'''
	def Clone (self):
		return self.__class__ ()
		
	def TransferFromWindow (self):
		return True
		
	def TransferToWindow (self):
		return True

#===========================================================
class BookLabelDialog (wx.Dialog):
	'''Dialog to enter labels for capture-page displays.'''
	def __init__ (self, parent, value, capturedata=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'Trace Legend')
		self.label_ctrl = wx.TextCtrl (self, -1, value)
		self.label_ctrl.SetFocus()
		self.label_ctrl.SetSelection (-1, -1)
		
		ts = wx.BoxSizer (wx.VERTICAL)
		if capturedata is not None:
			ts.Add (self._capture_details (capturedata), 0, wx.TOP, 10)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add (wx.StaticText (self, wx.ID_ANY, 'Capture Label'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		hs.Add (self.label_ctrl, 1, wx.EXPAND)
		ts.Add (hs, 0, wx.EXPAND|wx.ALL, 10)
		
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND|wx.TOP, 10)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
		
	def _capture_details (self, data):
		gs = wx.FlexGridSizer (0,2)
		gs.SetHGap (10)
		def data_line (caption, text):
			gs.Add (wx.StaticText (self, -1, caption), 0, wx.ALIGN_RIGHT)
			gs.Add (wx.StaticText (self, -1, text), 0, wx.ALIGN_CENTER)
		data_line ('Captured', time.ctime (data.capture_time))
		data_line ('Rate', frequency_with_units (data.frequency))
		data_line ('Size', str (data.read_count))
		data_line ('Delayed', str (data.delay_count))
		data_line ('Mask', hex (data.channel_mask))
		return gs
			
	def SetValue (self, label_string):
		self.label_ctrl.SetValue (label_string)
				
	def GetValue (self):
		return self.label_ctrl.GetValue()

#===========================================================
class LabelDialog (wx.Dialog):
	'''Dialog to enter labels for trace displays.'''
	def __init__ (self, parent, valuedict=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'Trace Legend')
		self.label_ctls = [wx.TextCtrl (self, -1, '') for i in xrange (32)]
		if valuedict is not None:
			self.SetValue (valuedict)
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ic = list (enumerate (self.label_ctls))
		hs = wx.BoxSizer (wx.HORIZONTAL)
		for j in xrange (0, 32, 8):
			gs = wx.FlexGridSizer (8, 2)
			gs.AddGrowableCol (1)
			for k  in xrange (j, j+8):
				i, ctl = ic[k]
				gs.Add (wx.StaticText (self, -1, str (i)), 0
					, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER|wx.LEFT, 10)
				gs.Add (ctl, 1, wx.LEFT, 5)
			hs.Add (gs, 1)
		ts.Add (hs, 0, wx.EXPAND|wx.ALL, 10)
		
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND|wx.TOP, 10)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
			
	def SetValue (self, valuedict):
		for k, v in valuedict.items():
			try:
				c = self.label_ctls[k]
			except (IndexError, TypeError):
				continue
			c.SetValue (v)
				
	def GetValue (self):
		return dict ( [ (i, ctl.GetValue()) for i, ctl in enumerate (self.label_ctls) if ctl.GetValue() ] )

#===========================================================
class MetadataDialog (wx.Dialog):
	'''Dialog to set time scale options.'''
	def __init__ (self, parent, metadata):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'SUMP Device Metadata')
		
		ts = wx.BoxSizer (wx.VERTICAL)
		if not metadata:
			ts.Add (wx.StaticText (self, -1, 'No Metadata was returned.'), 0, wx.ALL, 10)
			
		else:
			from sump_metadata import headings
			gs = wx.FlexGridSizer (0, 3)
			gs.SetHGap (10)
			for token, data in metadata:
				gs.Add (wx.StaticText (self, -1, hex(token)))
				gs.Add (wx.StaticText (self, -1, headings.get (token, '')))
				gs.Add (wx.StaticText (self, -1, str (data)))
			ts.Add (gs, 1, wx.ALIGN_CENTER|wx.ALL, 10)
			
		ts.Add (self.CreateButtonSizer (wx.OK), 0, wx.EXPAND)
		
		self.SetSizer (ts)
		self.SetInitialSize()
		

#===========================================================
class TimeScaleDialog (wx.Dialog):
	'''Dialog to set time scale options.'''
	def __init__ (self, parent, automatic=False, tick=100, unit=1000000):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'Time Axis')
		
		#~ self.units = 1
		self.default_ctrl = wx.CheckBox (self, wx.ID_ANY, 'Automatic')
		self.tick_size_ctrl = wx.TextCtrl (self, wx.ID_ANY, '')
		self.tick_unit_ctrl = wx.ComboBox (self, wx.ID_ANY, style=wx.CB_READONLY)
		for txt, num in zip (time_units_text, time_units_values):
			self.tick_unit_ctrl.Append (txt, clientData=num)
		self.tick_unit_ctrl.SetSelection (1)
		self.tick_unit_ctrl.SetMinSize ((60, -1))
		
		#~ if values is not None:
		self.SetValue (automatic, tick, unit)
		
		tick_sizer = wx.BoxSizer (wx.HORIZONTAL)
		tick_sizer.Add (wx.StaticText (self, wx.ID_ANY, 'Interval'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
		tick_sizer.Add (self.tick_size_ctrl, 3, wx.RIGHT, 5)
		tick_sizer.Add (self.tick_unit_ctrl, 0)
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (self.default_ctrl , 0)
		ts.Add (tick_sizer, 1, wx.EXPAND|wx.ALL, 10)
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
		
	def GetValue (self):
		return (self.default_ctrl.GetValue(), 
				int (self.tick_size_ctrl.GetValue()),
				self.tick_unit_ctrl.GetClientData (self.tick_unit_ctrl.GetSelection())
			)
		
	def SetValue (self, automatic, tick, unit):
		self.default_ctrl.SetValue (automatic)
		self.tick_size_ctrl.SetValue (str (tick))
		self.tick_unit_ctrl.SetStringSelection (time_units_text[time_units_values.index (unit)])
		

#===========================================================
class TracePropertiesDialog (wx.Dialog):
	'''Enter/edit the properties of a single trace.'''
	def __init__ (self, parent, trace, label):
		wx.Dialog.__init__ (self, parent, -1, title='Trace# %d' % (trace,))
		
		vs = wx.BoxSizer (wx.VERTICAL)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add (wx.StaticText (self, -1, 'Label'), 0, wx.ALIGN_CENTER_VERTICAL, 10)
		hs.Add ((20, 0), 0, 0)
		self.label_edit = wx.TextCtrl (self, -1, value=label)
		self.label_edit.SetFocus()
		self.label_edit.SetSelection (-1, -1)
		hs.Add (self.label_edit, 1, 0)
		vs.Add (hs, 0, wx.EXPAND)
		
		vs.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (vs)
		vs.Fit (self)
		vs.SetSizeHints (self)
		
	def GetValue (self):
		return self.label_edit.GetValue ()
		

#===========================================================
class ZoomDialog (wx.Dialog):
	'''Dialog to directly set zoom for trace graphs.'''
	def __init__ (self, parent, zoom):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY)
		
		zoom_sizer = wx.BoxSizer (wx.HORIZONTAL)
		zoom_sizer.Add (wx.StaticText (self, wx.ID_ANY, 'Zoom'), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		self.zoom_ctrl = wx.TextCtrl (self, wx.ID_ANY, str (zoom), validator=ZoomValidator())
		self.zoom_ctrl.SetFocus()
		self.zoom_ctrl.SetSelection (-1, -1)
		zoom_sizer.Add (self.zoom_ctrl, 1)
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (zoom_sizer, 1, wx.EXPAND|wx.BOTTOM, 10)
		ts.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL), 0, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		ts.SetSizeHints (self)
		
	def GetValue (self):
		return self.zoom_ctrl.GetValue()
		
class ZoomValidator (SimpleValidator):
	'''Validate correct zoom entry.'''
	def Validate (self, parent):
		ctrl = self.GetWindow()
		t = ctrl.GetValue()
		result = True
		try:
			v = int (t)
		except ValueError:
			result = False
		result = result and (v >= 1)
		if not result:
			wx.MessageBox ('Zoom value must be an integer >= 1.', 'Bad Input', wx.ICON_ERROR|wx.CANCEL)
			ctrl.SetFocus()
			ctrl.SetSelection (-1, -1)
		return result
