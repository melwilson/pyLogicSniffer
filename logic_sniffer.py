#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''Client display program for Open Bench Logic Sniffer 
and other SUMP analyzers.
Copyright © 2011, Mel Wilson mwilson@melwilsonsoftware.ca
This file is part of pyLogicSniffer.

pyLogicSniffer is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

pyLogicSniffer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with pyLogicSniffer.  If not, see
<http://www.gnu.org/licenses/>.
'''

import wx, wx.grid
import numpy as np
import os, sys
from serial import SerialException
import sump
import sump_config_file
from sump_settings import SumpDialog, ID_CAPTURE
from logic_sniffer_classes import TraceData
from logic_sniffer_dialogs import BookLabelDialog, LabelDialog, TimeScaleDialog, TracePropertiesDialog, ZoomDialog
import logic_sniffer_save

time_units_text = ['nS', u'μS', 'mS', 'S']
time_units_values = [1000000000, 1000000, 1000, 1]

# File dialog wildcard string for SUMP saved settings ..
sump_ini_wildcards = 'SUMP INI files|*.sump.ini|INI files (*.ini)|*.ini|all files (*)|*'
# same again for comma-separated-values ..
csv_wildcards = 'CSV files (*.csv)|*.csv|all files (*)|*'
		

#===========================================================
def log_error (msg):
	sys.stderr.write ('\n\n' + msg + '\n')
	sys.stderr.flush()

#===========================================================
class PluginTool (object):
	'''Collect info for a loaded plugin.'''
	def __init__ (self, tool_id, tool_module, tool_settings):
		self.idval = tool_id
		self.module = tool_module
		self.settings = tool_settings
		
#===========================================================
class TimeLegend (wx.Panel):
	'''Display a time scale above the trace display.'''
	def __init__ (self, parent):
		wx.Panel.__init__ (self, parent, -1, size=(-1,20), style=wx.FULL_REPAINT_ON_RESIZE)
		self.SetFont (wx.Font (10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.data = None
		self.scale = None
		self.zoom = 1
		self._bitmap = None
		self.sample_scroll = self.sample_offset = 0
		self.Bind (wx.EVT_PAINT, self.OnPaint)
		self.Bind (wx.EVT_SIZE, self.OnSize)
		
	def OnPaint (self,evt):
		pdc = wx.PaintDC (self)
		if self._bitmap is not None:
			dc = wx.ClientDC (self)
			mdc = wx.MemoryDC (self._bitmap)
			w, h = self.GetClientSizeTuple ()
			dc.Blit (0, 0, w, h, mdc, self.sample_offset, 0)
			
	def OnSize (self, evt):
		if self.data is not None:
			width, height = evt.GetSize ()
			self.scale = float (width) / self.data.read_count
			self._set_sample_offset()
			wx.CallAfter (self.ReDraw)
		evt.Skip()
			
	def _draw_legend (self, dc, width, height):
		if self.data is not None:
			dc.SetBackground (wx.Brush (self.GetBackgroundColour()))
			dc.SetTextBackground (self.GetBackgroundColour())
			dc.SetTextForeground ('BLACK')
			dc.SetFont (self.GetFont())
			dc.Clear()
			scale = self.scale
			data = self.data
			zoom = self.zoom
			scalezoom = scale * zoom
			
			def sample_time (sample):
				'''Return time of occurence of sample #sample.'''
				return float (sample)/data.frequency*time_units_values[1]
				
			def place_text (text, sample):
				tw, th = dc.GetTextExtent (text)
				tx = min (width-tw, max (0, int (sample * scalezoom) - tw/2))
				dc.DrawText (text, tx, 0)
				
			place_text ('%g%s' % (sample_time (data.delay_count-data.read_count), time_units_text[1]), 0)
			place_text ('%g%s' % (sample_time (data.delay_count), time_units_text[1]), data.read_count-1)
			if 0 < data.delay_count < data.read_count:
				place_text ('0', data.read_count - data.delay_count)
		
	def ReDraw (self):
		w, h = self.GetClientSizeTuple()
		w *= self.zoom
		self._bitmap = wx.EmptyBitmap (w, h)
		dc = wx.MemoryDC (self._bitmap)
		self._draw_legend (dc, w, h)
		del dc
		self.Refresh()
		
	def SetData (self, data):
		self.data = data
		width, height = self.GetClientSizeTuple ()
		self.scale = float (width) / self.data.read_count
		self.zoom = 1
		self.sample_scroll = 0
		self._set_sample_offset()
		
		self.ReDraw()
		
	def ScrollToSample (self, sample):
		self.sample_scroll = sample
		self._set_sample_offset()
		self.Refresh()
		
	def _set_sample_offset (self):
		self.sample_offset = self.sample_scroll * self.scale * self.zoom
		
	def SetZoom (self, zoom):
		self.zoom = zoom
		self._set_sample_offset()
		self.ReDraw()
		
class TraceLegend (wx.Panel):
	'''Display channel numbers and legends beside the trace display.'''
	def __init__ (self, parent, trace_max, trace_height, legends):
		wx.Panel.__init__ (self, parent, -1)
		self.legends = legends
		self.trace_max = trace_max
		self.trace_height = trace_height
		self.SetForegroundColour (wx.RED)
		self.captions = []
		for i in xrange (trace_max):
			self.captions.append (wx.StaticText (self, -1, str (i), pos=(0, 5+i*trace_height)))
		w = max (c.GetSizeTuple()[0] for c in self.captions)
		self.SetMinSize ((w, -1))
		
	def ScrollToTrace (self, trace):
		pass
		
	def SetData (self, data):
		pass
		
	def SetLegend (self, trace, legend):
		self.legends[trace] = legend
		self.captions[trace].SetLabel ('%d %s' % (trace, legend))
		w = max (c.GetSizeTuple()[0] for c in self.captions)
		self.SetMinSize ((w, -1))

class TraceGraphs (wx.Window):
	'''Actual data graphs.'''
	TRACE_HEIGHT = 20
	TRACE_MAX = 16
	def __init__ (self, parent):
		wx.Window.__init__ (self, parent, wx.ID_ANY)
		self._bitmap = None
		self.data = None
		self.tracedata = [None]*self.TRACE_MAX
		self.scale = None
		self.zoom = 1
		self.sample_scroll = self.sample_offset = 0
		self.trace_scroll = self.trace_offset = 0
		
		self.SetBackgroundColour ("WHITE")
		self.text_font = wx.Font (10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL
				, wx.FONTWEIGHT_NORMAL)
		self.Bind (wx.EVT_PAINT, self.OnPaint)
		self.Bind (wx.EVT_SIZE, self.OnSize)
		
		self.SetMinSize ((400, 300))
		
	def CalcXSample (self, x):
		if self.data is None:
			return None
		sample = (x + self.sample_offset) / (self.scale * self.zoom)
		return round (sample)
		
	def CalcXSampleTime (self, x):
		if self.data is None:
			return None
		sample = self.CalcXSample (x)
		sample_time = float (sample - self.data.read_count + self.data.delay_count) / self.data.frequency * time_units_values[1]
		return sample_time
			
	def OnPaint (self, evt):
		pdc = wx.PaintDC (self)
		if self._bitmap is not None:
			dc = wx.ClientDC (self)
			mdc = wx.MemoryDC (self._bitmap)
			w, h = self.GetClientSizeTuple ()
			dc.Blit (0, 0, w, h, mdc, self.sample_offset, self.trace_offset)
			
	def OnSize (self, evt):
		if self.data is not None:
			width, height = evt.GetSize ()
			self.scale = float (width) / self.data.read_count
			self._set_sample_offset()
			wx.CallAfter (self.ReDraw)
		evt.Skip()
		
	def _draw_traces (self, dc):
		data = self.data
		dc.Clear()
		
		# Mark Time 0
		dc.SetPen (wx.GREEN_PEN)
		xz = int ((data.read_count-data.delay_count) * self.scale * self.zoom)	# x-ordinate of time 0
		y1 = self.TRACE_MAX*self.TRACE_HEIGHT
		dc.DrawLine (xz,0, xz,y1)
		
		dc.SetPen (wx.BLACK_PEN)
		scale = self.scale * self.zoom
		traceheight = self.TRACE_HEIGHT
		thm1 = traceheight-1
		thm6 = traceheight-6	# Y-axis height from 0-bit to 1-bit
		
		def draw_single_trace (dc, tracedata, ybase):
			dc.DrawLines (tracedata, 0, ybase)
			
		for channel in xrange (self.TRACE_MAX):
			if self.tracedata [channel] is None:
				tl = data.channel_data (channel)	# logical 0..1 trace values for the channel
				tl = traceheight - tl * thm6			# Y-axis position for each trace point
				self.tracedata[channel] = np.column_stack ( (np.arange (len (tl)), tl) )
			draw_single_trace (dc, self.tracedata[channel]*(scale,1), channel*traceheight)
			
	def ReDraw (self):
		if self.data is not None:
			width = self.data.read_count * self.scale * self.zoom
			height = self.TRACE_HEIGHT * self.TRACE_MAX
			self._bitmap = wx.EmptyBitmap (width, height)
			dc = wx.MemoryDC (self._bitmap)
			self._draw_traces (dc)
			del dc
			self.Refresh()
		
	def ScrollToSample (self, sample):
		self.sample_scroll = sample
		self._set_sample_offset()
		self.Refresh()
		
	def ScrollToTrace (self, trace):
		pass
		
	def _set_sample_offset (self):
		self.sample_offset = self.sample_scroll * self.scale * self.zoom
		
	def SetData (self, data):
		self.data = data
		self.zoom =1
		width, height = self.GetClientSizeTuple ()
		self.scale = float (width) / self.data.read_count
		self._set_sample_offset()
		self.tracedata = [None]*self.TRACE_MAX
		self.ReDraw()
		
		sys.stderr.write ('TraceGraphs.SetData scale: %f\n' % (self.scale,)); sys.stderr.flush()
		sys.stderr.write ('TraceGraphs.SetData Zero at %d\n' % (data.read_count - data.delay_count,)); sys.stderr.flush()
		
	def SetZoom (self, zoom):
		old_zoom = self.zoom
		self.zoom = zoom
		self._set_sample_offset()
		self.ReDraw()
		
		
#-----------------------------------------------------------
class TraceWindow (wx.Panel):
	'''Pageable graph with X- and Y-axis legends and plotting area for traces.'''
	def __init__ (self, parent, legends=None):
		wx.Panel.__init__ (self, parent, wx.ID_ANY
			, style=wx.HSCROLL|wx.VSCROLL|wx.ALWAYS_SHOW_SB
			)
		if legends is None:
			legends = {}
		self.legends = legends
		self.zoom = 1
		self.timescroll = 0
		self.tracescroll = 0
		self.settings = sump.SumpDeviceSettings()
		self.tool_windows = []
		
		self.graphs = TraceGraphs (self)
		self.trace_legend = TraceLegend (self, self.graphs.TRACE_MAX, self.graphs.TRACE_HEIGHT, self.legends)
		self.time_legend = TimeLegend (self)
		
		ts = wx.FlexGridSizer (2, 2)
		ts.AddGrowableRow (1)
		ts.AddGrowableCol (1)
		ts.Add ((0,0), 0, 0)
		ts.Add (self.time_legend, 1, wx.EXPAND)
		ts.Add (self.trace_legend, 1, wx.EXPAND)
		ts.Add (self.graphs, 1, wx.EXPAND)

		self.graphs.Bind (wx.EVT_RIGHT_DOWN, self.OnGraphRightClick)
		self.trace_legend.Bind (wx.EVT_RIGHT_DOWN, self.OnGraphRightClick)
		self.Bind (wx.EVT_SIZE, self.OnSize)
		self.Bind (wx.EVT_SCROLLWIN, self.OnScroll)
		
		self.SetAutoLayout (True)
		self.SetSizer (ts)
		ts.Fit (self)
		
		self.SetScrollbar (wx.HORIZONTAL	# will ultimately be calibrated in samples
			, position = self.timescroll
			, thumbSize= 4096
			, range = 4096
			, refresh=True)
		self.SetScrollbar (wx.VERTICAL	# calibrate the vertical scrollbar in traces
			, position = self.tracescroll
			, thumbSize= self.graphs.TRACE_MAX
			, range = self.graphs.TRACE_MAX
			, refresh=True)
			
	def AddToolWindow (self, tool):
		self.tool_windows.append (tool)
		tool.Show()
			
	def _calibrate_time (self):
		data = self.graphs.data
		if data is not None:
			self.SetScrollbar (wx.HORIZONTAL
				, position = self.timescroll
				, thumbSize= data.read_count / self.zoom
				, range = data.read_count
				, refresh=True)

	def Destroy (self):
		for t in self.tool_windows:
			t.Destroy()
		wx.Panel.Destroy (self)
		
	def GetData (self):
		'''Return the sample data set for this trace window.'''
		return self.graphs.data
		
	def OnGraphRightClick (self, evt):
		trace = evt.m_y / self.graphs.TRACE_HEIGHT + self.tracescroll
		if 0 <= trace < self.graphs.TRACE_MAX:
			d = TracePropertiesDialog (self, trace, self.legends.get (trace, ''))
			if wx.ID_OK == d.ShowModal():
				self.trace_legend.SetLegend (trace, d.GetValue())
				s = self.GetContainingSizer()
				if s:
					s.Fit (self)
				
	def OnScroll (self, evt):
		spos = evt.GetPosition()
		orientation = evt.GetOrientation()
		if orientation == wx.HORIZONTAL:
			# spos is the sample number to show at the left of the display
			self.graphs.ScrollToSample (spos)
			self.time_legend.ScrollToSample (spos)
			self.timescroll = spos
		elif orientation == wx.VERTICAL:
			# spos is the trace number to show at the top of the display
			self.graphs.ScrollToTrace (spos)
			self.trace_legend.ScrollToTrace (spos)
			self.tracescroll = spos
				
	def OnSize (self, evt):
		wx.CallAfter (self._calibrate_time)
		evt.Skip()
		
	def RemoveToolWindow (self, tool):
		keepers = []
		for t in self.tool_windows:
			if t is not tool:
				keepers.append (t)
		self.tool_windows[:] = keepers
		
	def SetData (self, data):
		self.graphs.SetData (data)
		self.time_legend.SetData (data)
		self.trace_legend.SetData (data)
		self._calibrate_time ()
		
	def SetTitle (self, title):
		for tw in self.tool_windows:
			tw.SetTitle (title)
		
	def SetZoom (self, zoom):
		self.zoom = max (1, zoom)
		self.graphs.SetZoom (zoom)
		self.time_legend.SetZoom (zoom)
		self._calibrate_time ()
				
	def ZoomIn (self, factor):
		self.SetZoom (self.zoom * factor)
		
	def ZoomOut (self, factor):
		try:
			self.SetZoom (self.zoom / factor)
		except ZeroDivideError:
			pass
		

#===========================================================
class MyFrame (wx.Frame):
	'''Top application frame.'''
	def __init__ (self, plugin_tools=()):
		wx.Frame.__init__ (self, None, wx.ID_ANY, 'Logic Sniffer')
		self.traces = None
		self.plugins = []
		self.capture_serial = 0
		
		self.timescale_auto = True
		self.timescale_tick = 1000
		self.timescale_unit = 1000000
		
		self.tracebook = wx.Notebook (self, wx.ID_ANY)
		self._new_capture_page()
			
		self.SetMenuBar (self._main_menu())
		self.tracebook.Bind (wx.EVT_RIGHT_DOWN, self.OnBookRClick)
		
		if verbose_flag:	print 'Plugins:', repr (plugin_tools)
		self._load_plugins (plugin_tools)
		
		statusbar = wx.StatusBar (self)
		statusbar.SetFieldsCount (4)
		self.SetStatusBar (statusbar)
		
		top_sizer = wx.BoxSizer (wx.VERTICAL)
		top_sizer.Add (self.tracebook, 1, wx.EXPAND)
		
		self.SetAutoLayout (True)
		self.SetSizer (top_sizer)
		top_sizer.Fit (self)
		top_sizer.SetSizeHints (self)
		
	def _load_plugins (self, registered_plugin_tools):
		'''Finish off the main menu with external plugin modules.'''
		for pt in registered_plugin_tools:
			if not pt:	# glitches in option handling can give us empty module names
				continue
			module = __import__ (pt)
			mid = wx.NewId()
			self.plugins.append ( PluginTool (mid, module, registered_plugin_tools[pt]) )
			menubar = self.GetMenuBar()
			tool_menu = menubar.GetMenu (menubar.FindMenu ('&Tools'))
			tool_menu.Append (mid, module.tool_menu_string)
			wx.EVT_MENU (self, mid, self.OnToolSelection)
		
	def _main_menu (self):
		'''Quasi-boilerplate to create the main menu.'''
		menubar = wx.MenuBar ()
		
		def append_bound_item (menu, handler, item='', itemid=-1):
			'''Bind a handler to a new menu item.'''
			if itemid == -1:
				itemid = wx.NewId()
			menu.Append (itemid, item)
			wx.EVT_MENU (self, itemid, handler)
			
		filemenu = wx.Menu()
		menubar.Append (filemenu, '&File')
		append_bound_item (filemenu, self.OnFileNew, itemid=wx.ID_NEW)
		append_bound_item (filemenu, self.OnFileOpen, itemid=wx.ID_OPEN)
		append_bound_item (filemenu, None, itemid=wx.ID_SAVE)
		append_bound_item (filemenu, self.OnFileSaveAs, itemid=wx.ID_SAVEAS)
		append_bound_item (filemenu, self.OnFileExportCsv, '&Export to CSV...')
		filemenu.AppendSeparator ()
		append_bound_item (filemenu, self.OnFileLoadSumpConfig, '&Load SUMP Config...')
		append_bound_item (filemenu, self.OnFileSaveSumpConfigAs, 'Sa&ve SUMP Config...')
		filemenu.AppendSeparator ()
		append_bound_item (filemenu, self.OnFileClose, '&Close Tab', wx.ID_CLOSE)
		filemenu.AppendSeparator()
		#~ append_bound_item (filemenu, None, itemid=wx.ID_PRINT)
		#~ append_bound_item (filemenu, None, itemid=wx.ID_PAGE_SETUP)
		filemenu.AppendSeparator()
		append_bound_item (filemenu, self.OnFileExit, itemid=wx.ID_EXIT)
		
		viewmenu = wx.Menu()
		menubar.Append (viewmenu, '&View')
		append_bound_item (viewmenu, self.OnViewLegend, '&Legend')	# edit trace legends
		append_bound_item (viewmenu, self.OnViewTimeScale, '&Time Scale ...')	# edit time scale units
		append_bound_item (viewmenu, self.OnViewZoom, '&Zoom ...')
		append_bound_item (viewmenu, self.OnViewZoomIn, 'Zoom &In')
		append_bound_item (viewmenu, self.OnViewZoomOut, 'Zoom &Out')
		
		devicemenu = wx.Menu()
		menubar.Append (devicemenu, '&Device')
		append_bound_item (devicemenu, self.OnDeviceCapture, '&Capture')	# capture with new settings
		append_bound_item (devicemenu, self.OnDeviceRepeat, '&Repeat')	#capture with same settings as before
		devicemenu.AppendSeparator()
		append_bound_item (devicemenu, self.OnDeviceSimulate, '&Simulate')	# Simulate a capture with synthesized bits
		devicemenu.AppendSeparator()
		append_bound_item (devicemenu, self.OnDeviceSetup, 'Se&tup')	# set port and baud rate
		
		toolmenu = wx.Menu()
		menubar.Append (toolmenu, '&Tools')
		append_bound_item (toolmenu, self.OnToolsTraces, '&Traces')	# default trace-graphing screen
		
		helpmenu = wx.Menu()
		menubar.Append (helpmenu, '&Help')
		append_bound_item (helpmenu, self.OnHelpAbout, itemid=wx.ID_ABOUT)
		return menubar
			
	def _captured_sump_data (self, settings, data):
		return TraceData (settings.clock_rate / settings.divider	# sample frequency in Hz
				, settings.read_count	# number of samples
				, settings.delay_count	# number of samples after trigger
				, settings.channel_groups	# mask for suppressed channel groups
				, data			# array of 32-bit readings
				)
		
	def _new_capture_page (self):
		new_trace = TraceWindow (self.tracebook)
		self.capture_serial += 1
		self.tracebook.AddPage (new_trace, 'Capture %d' % (self.capture_serial,), select=True)
		new_trace.graphs.Bind (wx.EVT_MOTION, self.OnGraphMouseMotion)
		return new_trace
		
	def _selected_page (self):
		return self.tracebook.GetCurrentPage()
				
	def DoCapture (self):
		tw = self._selected_page()
		wx.BeginBusyCursor()
		sniffer.send_settings (tw.settings)
		try:
			d = sniffer.capture (tw.settings)
		except KeyboardInterrupt:
			sniffer.reset()
			d = None
			sys.stderr.write ('interrupted\n'); sys.stderr.flush()
		wx.EndBusyCursor()
		if d is not None:
			sys.stderr.write ('captured\n'); sys.stderr.flush()
			tw.SetData (self._captured_sump_data (tw.settings, d))
		
	def DoSimulate (self):
		tw = self._selected_page()
		d = self.data = np.arange (tw.settings.read_count, dtype=np.uint32)
		sys.stderr.write ('simulated\n'); sys.stderr.flush()
		tw.SetData (self._captured_sump_data (tw.settings, d))
		
	def OnBookRClick (self, evt):
		'''Handle right-click on one of the notebook's page tabs.'''
		ctrl = evt.GetEventObject()
		page, flags = ctrl.HitTest ((evt.m_x, evt.m_y))
		if page != wx.NOT_FOUND:
			d = BookLabelDialog (self, ctrl.GetPageText (page))
			if d.ShowModal() == wx.ID_OK:
				title = d.GetValue()
				ctrl.SetPageText (page, title)
				self.tracebook.GetPage (page).SetTitle (title)
			d.Destroy()
		
	def OnDeviceCapture (self, evt):
		tw = self._selected_page()
		d = SumpDialog (self, tw.settings)
		while True:
			result = d.ShowModal()
			if result in (wx.ID_OK, ID_CAPTURE):
				if d.Validate():
					d.ValuesToSettings (tw.settings)
					if result == ID_CAPTURE:
						self.DoCapture()
					break
			else: 
				break
		d.Destroy()
		
	def OnDeviceSimulate (self, evt):
		tw = self._selected_page()
		d = SumpDialog (self, tw.settings)
		while True:
			result = d.ShowModal()
			if result in (wx.ID_OK, ID_CAPTURE):
				if d.Validate():
					d.ValuesToSettings (tw.settings)
					if result == ID_CAPTURE:
						self.DoSimulate()
					break
			else: 
				break
		d.Destroy()
		
	def OnDeviceRepeat (self, evt):
		self.DoCapture()
		
	def OnDeviceSetup (self, evt):
		pass
		
	def OnFileClose (self, evt):
		'''Close the currently selected sample page.'''
		x = self.tracebook.GetSelection ()
		if x > -1:
			self.tracebook.DeletePage (x)
		
	def OnFileExit (self, evt):
		self.Destroy()
		
	def OnFileExportCsv (self, evt):
		'''Save the current SUMP capture to a CSV file.'''
		d = wx.FileDialog (self		
				, wildcard=csv_wildcards
				, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		page = self._selected_page()
		if d.ShowModal() == wx.ID_OK:
			logic_sniffer_save.to_csv (d.GetPath(), page.graphs.data)
		d.Destroy()
		
	def OnFileLoadSumpConfig (self, evt):
		'''Load the current SUMP settings from a config file.'''
		d = wx.FileDialog (self, 'Load SUMP Settings from...'
				, wildcard=sump_ini_wildcards
				, style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		page = self._selected_page()
		if hasattr (page, 'config_path'):
			d.SetPath (page.config_path)
		if d.ShowModal() == wx.ID_OK:
			config_path = d.GetPath()
			page.settings = sump_config_file.load_config (config_path)
			page.config_path = config_path
		d.Destroy()
		
	def OnFileNew (self, evt):
		self._new_capture_page()
		
	def OnFileOpen (self, evt):
		'''Load previously saved data into a SUMP Capture page.'''
		d = wx.FileDialog (self, style=wx.FD_OPEN)
		if d.ShowModal() == wx.ID_OK:
			tw = self._selected_page()
			if tw.GetData() is not None:
				tw = self._new_capture_page()
			sample = logic_sniffer_save.from_file (d.GetPath())
			tw.SetData (sample)
		d.Destroy()
		
	def OnFilePageSetup (self, evt):
		#~ d = wx.PageSetupDialog (self, self.page_setup_dialog_data)
		#~ if d.ShowModal() == wx.ID_OK:
			#~ self.page_setup_dialog_data = d.GetPageSetupDialogData()
		#~ d.Destroy()
		pass
		
	def OnFilePrint (self, evt):
		#~ d = wx.PrintDialog (self, self.print_dialog_data)
		#~ if d.ShowModal() == wx.ID_OK:
			#~ self.print_dialog_data = d.GetPrintDialogData()
		#~ d.Destroy()
		pass
		
	def OnFileSaveAs (self, evt):
		'''Save SUMP capture data into a file.'''
		d = wx.FileDialog (self, style=wx.FD_SAVE)
		page = self._selected_page()
		if d.ShowModal() == wx.ID_OK:
			logic_sniffer_save.to_file (d.GetPath(), page.graphs.data)
		d.Destroy()
		
	def OnFileSaveSumpConfigAs (self, evt):
		'''Save the current SUMP settings in a config file.'''
		d = wx.FileDialog (self, 'Save SUMP Settings to...'
				, wildcard=sump_ini_wildcards
				, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		page = self._selected_page()
		if hasattr (page, 'config_path'):
			d.SetPath (page.config_path)
		if d.ShowModal() == wx.ID_OK:
			config_path = d.GetPath()
			if config_path.endswith ('.sump'):
				config_path += '.ini'
			if not config_path.endswith ('.ini'):
				config_path += '.sump.ini'
			sump_config_file.save_config (config_path, page.settings)
			page.config_path = config_path
		d.Destroy()
		
	def OnGraphMouseMotion (self, evt):
		if evt.Moving():
			graphs = evt.GetEventObject()
			sample = graphs.CalcXSample (evt.m_x)
			sample_time = graphs.CalcXSampleTime (evt.m_x)
			if sample_time is not None:
				wx.CallAfter (self.GetStatusBar().SetStatusText, '%d -- %g%s' % (sample, sample_time, time_units_text[1]))
		evt.Skip()
		
	def OnHelpAbout (self, evt):
		wx.MessageBox (__doc__, 'About %s' % (os.path.split (__file__)[-1],), style=wx.ICON_INFORMATION|wx.OK)
		
	def OnToolSelection (self, evt):
		'''Open a page or window for the selected plugin analysis tool.'''
		event_id = evt.GetId()
		for plugin in self.plugins:
			if plugin.idval == event_id:
				break
		else:	# couldn't find requested plugin
			return
		dlg = plugin.module.AnalyzerDialog (self, plugin.settings)
		try:
			if dlg.ShowModal() == wx.ID_OK:
				if not dlg.Validate():
					return
				plugin.settings = dlg.GetValue()
				tw = self._selected_page()
				if hasattr (plugin.module, 'AnalyzerFrame'):
					title = self.tracebook.GetPageText (self.tracebook.GetSelection())
					frame = plugin.module.AnalyzerFrame (tw, plugin.settings, tw.graphs.data, title)
					tw.AddToolWindow (frame)
				else:
					page = plugin.module.AnalyzerPanel (self.tracebook, plugin.settings, tw.graphs.data)
					self.tracebook.AddPage (page, '%s %d' % (plugin.module.tool_title_string, self.tracebook.GetPageCount(),), select=True)
		finally:	# application might hang on shutdown if dlg crashes because of an error
			dlg.Destroy()
		
	def OnToolsTraces (self, evt):
		pass
		
	def OnViewLegend (self, evt):
		tw = self._selected_page()
		d = LabelDialog (self, tw.trace_legend.legends)
		if d.ShowModal() == wx.ID_OK:
			for k, v in d.GetValue().items():
				tw.trace_legend.SetLegend (k, v)
		d.Destroy()
		
	def OnViewTimeScale (self, evt):
		d = TimeScaleDialog (self, self.timescale_auto, self.timescale_tick, self.timescale_unit)
		if d.ShowModal() == wx.ID_OK:
			self.timescale_auto, self.timescale_tick, self.timescale_unit = d.GetValue()
		d.Destroy()
		
	def OnViewZoom (self, evt):
		tw = self._selected_page()
		d = ZoomDialog (self, tw.zoom)
		if d.ShowModal() == wx.ID_OK:
			if not d.Validate():
				return
			tw.SetZoom (int (d.GetValue()))
		d.Destroy()
		
	def OnViewZoomIn (self, evt):
		self._selected_page().ZoomIn (2)
		
	def OnViewZoomOut (self, evt):
		self._selected_page().ZoomOut (2)
	
class MyApp (wx.App):
	'''Application.'''
	def OnInit (self):
		frame = MyFrame (plugin_modules)
		frame.Show (True)
		self.SetTopWindow (frame)
		return True
		
#===========================================================
def print_configparser_contents (cfp):
	for section in cfp.sections():
		print section
		for opt in cfp.options (section):
			print '\t%s:\t%s' % (opt, cfp.get (section, opt))
			
def optional_path (*args):
	'''Return a joined path it all its components exist, else None.'''
	if None in args:
		return None
	else:
		return os.path.join (*args)
			
def str_to_list (s):
	if not s:
		return []
	else:
		return s.split (',')
	

if __name__ == '__main__':
	import ConfigParser, getopt, os, sys
	
	verbose_flag = False
	
	app_options = ConfigParser.ConfigParser ()
	app_options.add_section ('analyzer')
	app_options.set ('analyzer', 'baud',  str (sump.SUMP_BAUD))
	# apply options from user and application-level .ini files ..
	config_paths = []
	for d in (optional_path (os.environ.get ('HOME', None), '.logicsnifferrc')
			, optional_path (os.getcwd(), 'logic_sniffer.ini')):
		if d is not None and os.path.isfile (d):
			config_paths.append (d)
			app_options.read (d)
	# apply environment options ..
	for e, k in (('LOGICSNIFFER_PORT', 'port'), ('LOGICSNIFFER_BAUD', 'baud'),):
		if e in os.environ:
			app_options.set ('analyzer', k, os.environ[e])
	# apply options from command-line ..
	opts, args = getopt.getopt (sys.argv[1:], 'b:p:t:v', ['baud=', 'port=', 'tool=', 'verbose'])
	for o, v in opts:
		if o in ('-b', '--baud'):
			app_options.set ('analyzer', 'baud', v)
		elif o in ('-p', '--port'):
			app_options.set ('analyzer', 'port', v)
		elif o in ('-t', '--tool'):
			new_section = 'plugin '+v
			app_options.add_section (new_section)
			app_options.set (new_section, 'module',  v)
		elif o in ('-v', '--verbose'):
			verbose_flag = True
	if verbose_flag:
		for p in config_paths:
			print 'Config:', p
	if verbose_flag:
		print 'Options:'
		print_configparser_contents (app_options)
		print
	
	plugin_modules = {}
	for s in app_options.sections():
		if s.startswith ('plugin'):
			d = dict (app_options.items (s))
			if d['module'] not in plugin_modules:
				plugin_modules[d['module']] = d
			else:
				plugin_modules[d['module']].update (d)
	if verbose_flag:
		print 'Plugins:', plugin_modules

	sump_port = app_options.get ('analyzer', 'port')
	sump_baud = int (app_options.get ('analyzer', 'baud'))
	try:
		sniffer = sump.SumpInterface (sump_port, sump_baud)
	#~ except (IOError, Exception):
	except SerialException:
		log_error ('Error opening SUMP interface: %r' % (sys.exc_info(),))
		sniffer = None
	if sniffer is not None:
		if verbose_flag:
			sniffer.set_logfile (sys.stderr)
		sniffer.reset()
		if verbose_flag:
			print "SUMP ID:", sniffer.id_string()
	
	for a in args:
		pass
		
	if verbose_flag:	print 'Starting app'
	app = MyApp (0)
	if verbose_flag:	print 'Starting loop'
	app.MainLoop()
	sniffer.close()
