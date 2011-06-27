# -*- coding: UTF-8 -*-
'''Utilities for PyLogicSniffer analysis tools.
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
import time
import wx
		
def partial_bits (bitcount, data, msbfirst=True, bytelength=8, fillchar='x'):
	'''String representing the bits in a partially-filled byte.'''
	s = [str ((data >> i) & 1) for i in xrange (bitcount)]
	xfill = fillchar*(bytelength-bitcount)
	if msbfirst:
		return ''.join (s[::-1]) + xfill
	else:
		return xfill + ''.join(s)


#===========================================================	
class AnalyzerFrame (wx.Dialog):
	'''Free-standing window to display analyzer panel.'''
	def __init__ (self, parent, settings, tracedata, title='Data'):
		wx.Dialog.__init__ (self, parent, -1, ''
				, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX)
		self.SetTitle (title)
		self.settings = settings
		self.panel = self.CreatePanel (settings, tracedata)
		self.Bind (wx.EVT_CLOSE, self.OnClose)
		
		ts = wx.BoxSizer (wx.VERTICAL)
		ts.Add (wx.StaticText (self, -1, time.ctime (tracedata.capture_time)), 0, wx.EXPAND)
		ts.Add (wx.StaticText (self, -1, self.SettingsDescription (settings)), 0, wx.EXPAND)
		ts.Add (self.panel, 1, wx.EXPAND)
		button = wx.Button (self, -1, 'Done')
		button.Bind (wx.EVT_BUTTON, self.OnClose)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add ((1,1), 1)
		hs.Add (button, 0, wx.ALIGN_RIGHT)
		ts.Add (hs, 0, wx.EXPAND)
		
		self.SetSizer (ts)
		self.SetInitialSize()
		
	def CreatePanel (self, settings, tracedata):
		'''Return an instance of the analysis panel to include in this window.'''
		raise NotImplementedError
			
	def OnClose (self, evt):
		wx.CallAfter (self.GetParent().RemoveToolWindow,  self)
		self.Destroy()
		
	def SettingsDescription (self, settings):
		'''Return a string describing specific settings.'''
		raise NotImplementedError
		
		
#===========================================================	

class SimpleValidator (wx.PyValidator):
	'''Validators with simple, sensible defaults.'''
	def Clone (self):
		return self.__class__ ()
		
	def TransferFromWindow (self):
		return True
		
	def TransferToWindow (self):
		return True

	def DoValidation (self, converter, is_valid, error_message):
		'''For use by descendent classes Validate methods.'''
		ctrl = self.GetWindow()
		result = True
		try:
			v = converter (ctrl.GetValue())
		except ValueError:
			result =  False
		result = result and  is_valid (v)
		if not result:
			# make sure the erroneous field is selected on the screen
			ctrl.SetFocus()
			try:
				ctrl.SetSelection (-1, -1)	# try selecting editable text
			except TypeError:
				pass	# somehow this is not a text control
			wx.MessageBox (error_message, 'Bad Input', wx.ICON_ERROR|wx.CANCEL)
		return result
