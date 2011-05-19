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

import wx

class SimpleValidator (wx.PyValidator):
	'''Validators with simple, sensible defaults.'''
	def Clone (self):
		return self.__class__ ()
		
	def TransferFromWindow (self):
		return True
		
	def TransferToWindow (self):
		return True

	def DoValidation (self, converter, is_valid, error_message):
		'''For use by descendent classes' Validate methods.'''
		ctrl = self.GetWindow()
		result = True
		try:
			v = converter (ctrl.GetValue())
		except ValueError:
			result =  False
		result = result and  is_valid (v)
		if not result:
			wx.MessageBox (error_message, 'Bad Input', wx.ICON_ERROR|wx.CANCEL)
			# make sure the erroneous field is selected on the screen
			ctrl.SetFocus()
			ctrl.SetSelection (-1, -1)
		return result
