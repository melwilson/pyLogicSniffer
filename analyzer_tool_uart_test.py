# -*- coding: UTF-8 -*-
'''Unit tests for pyLogicSniffer UART analysis tool.
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
import unittest
import numpy as np
import analyzer_tool_uart as M

# Need unit tests for
# def expand_template (defs, bitwidth):
# def character_template (bitwidth, parity, length, stop):
# def character_score (samples, mask, val, (parity, length, stops), bitwidth):

class TestExpandTemplate (unittest.TestCase):
	'''Test expanding a series of RLE-terms given samples/bit.'''
	def test0 (self):
		'''Test special-case null inputs.'''
		expected = np.array ([], np.int8)
		
		# samples/bit = 0
		actual = M.expand_template (0, ((22,1),(33,0),(44,1)) )
		self.assertEqual (len (actual), 0)
		self.assert_((expected == actual).all())

		# empty RLE terms-series
		actual = M.expand_template (1, () )
		self.assertEqual (len (actual), 0)
		self.assert_((expected == actual).all())
		actual = M.expand_template (13, () )
		self.assertEqual (len (actual), 0)
		self.assert_((expected == actual).all())
		
		# zero run lengths
		actual = M.expand_template (1, ((0,1),) )
		self.assertEqual (len (actual), 0)
		self.assert_((expected == actual).all())
		actual = M.expand_template (1, ((0,0),) )
		self.assertEqual (len (actual), 0)
		self.assert_((expected != actual).all())
		
	def test1 (self):
		'''Test expansion of simple terms.'''
		# single bits all around
		expected = np.array ([0], np.int8)
		actual = M.expand_template (1, ((1,0),) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())
		
		expected = np.array ([1], np.int8)
		actual = M.expand_template (1, ((1,1),) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())

		# single RLE series
		expected = np.array ([0,0,0], np.int8)
		actual = M.expand_template (3, ((1,0),) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())
		
		expected = np.array ([1,1,1,1], np.int8)
		actual = M.expand_template (4, ((1,1),) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())
		
		# combined samples/bit and run lengths
		expected = np.array ([0,]*2*3, np.int8)
		actual = M.expand_template (2, ((3,0),) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())
		
		expected = np.array ([1,]*5*2, np.int8)
		actual = M.expand_template (5, ((2,1),) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())
		
	def test2 (self):
		'''Test combined samples/bit and RLE series.'''
		expected = np.array ([1,]*3 + [0,]*3*4 + [0,]*3*5 + [1,]*3*7, np.int8)
		actual = M.expand_template (3, ((1,1),(4,0),(5,0),(7,1)) )
		self.assertEqual (len (actual), len (expected))
		self.assert_((expected == actual).all())


class TestCharacterTemplate (unittest.TestCase):
	'''Test building RLE series from UART character parameters.'''
	def test0 (self):
		expected_mask = ((1,1), (8,0), (1,1))
		expected_value = ((1,0), (8,0), (1,1))
		actual_mask, actual_value = M.character_template (0, 8, 1)
		self.assertEqual (expected_mask, actual_mask)
		self.assertEqual (expected_value, actual_value)
		
		expected_mask = ((1,1), (5,0), (1,1), (1,1))
		expected_value = ((1,0), (5,0), (1,0), (1,1))
		actual_mask, actual_value = M.character_template (1, 5, 1)
		self.assertEqual (expected_mask, actual_mask)
		self.assertEqual (expected_value, actual_value)
		
		expected_mask = ((1,1), (9,0), (1,1), (2,1))
		expected_value = ((1,0), (9,0), (1,1), (2,1))
		actual_mask, actual_value = M.character_template (2, 9, 2)
		self.assertEqual (expected_mask, actual_mask)
		self.assertEqual (expected_value, actual_value)


class TestCharacterScore (unittest.TestCase):
	def test0 (self):
		pass
		
		
unittest.main()
