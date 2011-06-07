# -*- coding: UTF-8 -*-
'''Frame class to run a dialog for testing.
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

class SimpleTestFrame (wx.Frame):
	'''Top application frame.'''
	def __init__ (self, title=None, about_caption=None, about_text=None):
		if title is None:
			title = 'SimpleTestFrame title'
		if about_caption is None:
			about_caption = 'SimpleTestFrame about_caption'
		if about_text is None:
			about_text = 'SimpleTestFrame about_text'
		wx.Frame.__init__ (self, None, wx.ID_ANY, title)
		self.about_caption = about_caption
		self.about_text = about_text
		
		self.SetMenuBar (self._main_menu())
		button = wx.Button (self, wx.ID_ANY, '&Test')
		wx.EVT_MENU (self, wx.ID_ABOUT, self.OnHelpAbout)
		wx.EVT_MENU (self, wx.ID_EXIT,  self.OnFileExit)
		wx.EVT_MENU (self, wx.ID_NEW,  self.OnTest)
		button.Bind (wx.EVT_BUTTON, self.OnTest)
		
		top_sizer = wx.BoxSizer (wx.VERTICAL)
		top_sizer.Add (button, 0, wx.CENTER)
		
		self.SetAutoLayout (True)
		self.SetSizer (top_sizer)
		top_sizer.Fit (self)
		top_sizer.SetSizeHints (self)

	def _main_menu (self):
		'''Quasi-boilerplate to create the main menu.'''
		menu = wx.MenuBar ()
		filemenu = wx.Menu()
		filemenu.Append (wx.ID_NEW, '&Test')
		filemenu.AppendSeparator()
		filemenu.Append (wx.ID_EXIT, 'E&xit')
		menu.Append (filemenu, '&File')
		
		helpmenu = wx.Menu()
		helpmenu.Append (wx.ID_ABOUT, '&About')
		menu.Append (helpmenu, '&Help')
		return menu
		
	def OnFileExit (self, evt):
		self.Destroy()
		
	def OnHelpAbout (self, evt):
		wx.MessageBox (self.about_text, self.about_caption, style=wx.ICON_INFORMATION|wx.OK)
		
	def OnTest (self, evt):
		'''Overridable method to display a dialog.'''
		wx.MessageBox ('Override the OnTest method to display your dialog.', 'SimpleTestFrame')
