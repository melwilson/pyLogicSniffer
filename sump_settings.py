# -*- coding: UTF-8 -*-
'''Configuration dialog for a SUMP logic-analyzer device.
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
#~ import wx.richtext

ID_CAPTURE = wx.NewId()	# ID number for Capture button
	
def bimap (a, b):
	return dict (zip (a,b) + zip (b,a))
	
class LabelledValues (object):
	'''Associate SUMP parameter values with their representations in dialog boxes.'''
	def __init__ (self, labels, values):
		self.labels = labels
		self.values = values
		self.map = bimap (labels, values)
	def __getitem__ (self, key):
		return self.map [key]
	
baud_rate_settings = LabelledValues (
	['115200', '57600', '38400', '19200'], 
	[115200, 57600, 38400, 19200]
	)
delay_ratio_settings = LabelledValues (
	['0/100', '1/7', '25/75', '50/50', '75/25', '7/1', '100/0'],
	[1.0, .875, .75, .50, .25, .125, 0.0]
	)
frequency_settings = LabelledValues (
	['Hz', 'KHz', 'MHz', 'GHz'],
	[1, 1000, 1000000, 1000000000]
	)
number_scheme_settings = LabelledValues (
	['Inside', 'Outside', 'Test Mode'], 
	[0, 1, 2]
	)
recording_size_settings = LabelledValues (
	['16K', '8K', '4K', '2K', '1K', '512', '256', '128', '64'],
	[16384, 8192, 4096, 2048, 1024, 512, 256, 128, 64]
	)
sampling_clock_settings = LabelledValues (
	['Internal', 'External Rising', 'External Falling'],
	[0, 2, 3]
	)
sampling_rate_settings = LabelledValues (
	[
	'100MHz', '50MHz', '20MHz', '10MHz', '5MHz', '2MHz', '1MHz',
	'500KHz', '200KHz', '100KHz', '50KHz', '20KHz', '10KHz', '5KHz', '2KHz', '1KHz',
	'500', '200', '100', '50', '20', '10'
	],
	[
	100000000, 50000000, 20000000, 10000000, 5000000, 2000000, 1000000,
	500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000,
	500, 200, 100, 50, 20, 10
	]
	)
time_unit_settings = LabelledValues (
	['samples', 'seconds', 'msec', u'μsec', 'nsec'],
	[0, 1, 1000, 1000000, 1000000000]
	)
trigger_action_settings = LabelledValues (['Capture', 'Next Level'], [1, 0])
trigger_arm_settings = LabelledValues (['Immediately', 'Level 1', 'Level 2', 'Level 3'], [0, 1, 2, 3])
trigger_enable_settings = LabelledValues (['None', 'Simple', 'Complex'], [0, 1, 2])
trigger_mode_settings = LabelledValues (['Parallel', 'Serial'], [0, 1])
		
def _frequency_with_unit (rate):
	'''Return a frequency and unit string, normalized to Hz, KHz, MHz, etc. for easy reading.'''
	for val in frequency_settings.values:
		if float (rate) / val < 1000:
			return float (rate) / val, frequency_settings[val]
	val = frequency_settings.values[-1]
	return float (rate) / val, frequency_settings[val]


helptext = """
Connection Settings
* Port
* Baud
* Number Scheme

Analyzer Settings
* Sampling Clock
* Sampling Rate
* Recording Size
* Channel Group
* Filter
* Demux
* RLE

Trigger Settings
* Trigger
   - None -- sampling starts immediately
   - Simple -- sampling starts after a single Parallel or Serial trigger match
   - Complex --  sampling starts after a combination of trigger matches
* Pre/Post Ratio -- ratio of sampled bits before/after the trigger firing

* Stages
* * Arm
    - Immediately -- matching starts  immediately
    - Level .. -- matching starts when the trigger level reaches 1, 2, or 3
    
** Mode	'Parallel' to trigger on simultaneous levels in several channels, 'Serial' to trigger on sequential values in one channel.

** Channel -- the input channel which is tested in Serial triggering

** Mask	check each channel bit to be used in the trigger

** Value	checked bits match when '1', unchecked bits match when '0'

** Action	When the trigger fires, 'Capture'  starts sampling, 'Next Level' increments the trigger level.

** Delay	delay (in samples) between firing the trigger and the action.

"""

def settings_error (message):
	'''Common error reporting for settings.'''
	wx.MessageBox (message, 'SUMP Settings Error', style=wx.ICON_ERROR|wx.CANCEL)
	
def debug_output (s):
	#~ import sys
	#~ sys.stderr.write (s)
	#~ sys.stderr.flush()
	return
	

#===========================================================
class SumpTriggerPanel (wx.Panel):
	'''Tab-able panel with configuration for one of four Trigger Stages.'''
	def __init__ (self, parent, stage):
		if not (0 <= stage < 4):
			raise ValueError, 'Illegal trigger stage: %d' % (stage,)
		self.stage = stage
		wx.Panel.__init__ (self, parent, -1)
		self.InitDialog ()	# support validators for this panel's controls
		
		def labelled_ctl (sizer, label, ctl, sizer_ratio=0, sizer_flags=wx.EXPAND):
			hs = wx.BoxSizer (wx.HORIZONTAL)
			if label:
				hs.Add (wx.StaticText (self, wx.ID_ANY, label), 0, wx.ALIGN_CENTER_VERTICAL)
			hs.Add (ctl, 1, wx.EXPAND)
			sizer.Add (hs, sizer_ratio, sizer_flags)
			return ctl
		
		def labelled_ctl_list (sizer, label, ctls, sizer_ratio, sizer_flags=wx.EXPAND):
			hs = wx.BoxSizer (wx.HORIZONTAL)
			if label:
				hs.Add (wx.StaticText (self, wx.ID_ANY, label), 0, wx.ALIGN_CENTER_VERTICAL)
			for ctl, size in ctls:
				hs.Add (ctl, size, wx.EXPAND)
			sizer.Add (hs, sizer_ratio, sizer_flags)
			return ctl
		
		top_sizer = wx.BoxSizer (wx.VERTICAL)	# top-level sizer for the trigger panel
		
		self.arm_ctl = wx.RadioBox (self, wx.ID_ANY, 'Arm', choices=trigger_arm_settings.labels)
		self.mode_ctl = wx.RadioBox (self, wx.ID_ANY, 'Mode', choices=trigger_mode_settings.labels)
		self.serial_channel_ctl = wx.TextCtrl (self, -1, '0', validator=ChannelValidator())
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add (self.arm_ctl, 0)
		hs.Add ((50,0), 1)
		hs.Add (self.mode_ctl, 0)
		hs.Add ((50,0), 1)
		labelled_ctl (hs, 'Channel ', self.serial_channel_ctl, 0, wx.ALIGN_CENTER_VERTICAL )
				
		top_sizer.Add (hs, 0, 0)
		
		# controls for trigger masks and values
		self.mask_controls = [wx.CheckBox (self, -1) for i in xrange (32)]	# check boxes for bits 0..31
		self.value_controls = [wx.CheckBox (self, -1) for i in xrange (32)]	# check boxes for bits 0..31
		gs = wx.FlexGridSizer (3, 33)
		gs.Add ((0,0))	# empty corner over and beside legends
		for i in xrange (31,-1,-1):		# column legends
			gs.Add (wx.StaticText (self, -1, str (i)), 0, wx.ALIGN_CENTER)
			
		gs.Add (wx.StaticText (self, -1, ' Mask'), 0, wx.ALIGN_CENTER_VERTICAL)	# row legend
		for ctl in self.mask_controls[::-1]:	# bit 31 on the left, bit 0 on the right ..
			gs.Add (ctl)
			
		gs.Add (wx.StaticText (self, -1, ' Value'), 0, wx.ALIGN_CENTER_VERTICAL)	# row legend
		for ctl in self.value_controls[::-1]:	# bit 31 on the left, bit 0 on the right ..
			gs.Add (ctl)
			
		top_sizer.Add (gs, 0, wx.EXPAND)
		
		self.capture_ctl = wx.RadioBox (self, wx.ID_ANY, 'Action', choices=trigger_action_settings.labels)
		self.delay_ctl = wx.TextCtrl (self, -1, '0', validator=DelayValidator())
		self.delay_unit_ctl = wx.Choice (self, wx.ID_ANY, (-1,-1),(-1,-1) #, 'samples'
				, choices=time_unit_settings.labels, style=wx.CB_READONLY)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add (self.capture_ctl, 0)
		hs.Add ((50, 0), 0)
		labelled_ctl_list (hs, 'Delay ', [(self.delay_ctl, 1),(self.delay_unit_ctl, 0),], 0, wx.ALIGN_CENTER_VERTICAL)

		top_sizer.Add (hs, 0, wx.EXPAND)
		
		self.SetSizer (top_sizer)
		self.SetInitialSize()
		
	def _delay_from_units (self, sample_rate):
		'''Calcuate trigger delay in samples from control setting in samples or seconds.'''
		delay = float (self.delay_ctl.GetValue())
		delay_unit = time_unit_settings [self.delay_unit_ctl.GetStringSelection()]
		if delay_unit == 0:
			return int (delay)	# delay is in samples, 
		# convert delay in seconds to delay in samples
		return int ((delay * sample_rate) / delay_unit)
		
	def _delay_to_units (self, samples, delay_unit, sample_rate):
		'''Calculate control setting in samples or seconds from trigger delay in samples.'''
		if delay_unit == 0:
			return samples
		return (float (samples) * delay_unit) / sample_rate

	def _validate_delay (self, sample_rate):
		'''Validate a trigger delay, which may be expressed in seconds,
		given a configured sample rate.'''
		samples = self._delay_from_units (sample_rate)
		if 0 <= samples <= 65535:
			return True
			
		max_seconds = 65535.0/sample_rate
		for val in time_unit_settings.values[1:]:
			if max_seconds * val > 1:
				break
		error_message = ('''For sample rate %g %s\ndelay can't exceed %g %s'''
				% (_frequency_with_unit (sample_rate) + (max_seconds*val, time_unit_settings[val])))
		settings_error (error_message)
		# make sure the erroneous field is selected on the screen
		ctrl = self.delay_ctl
		ctrl.SetFocus()
		ctrl.SetSelection (-1, -1)
		notebook = self.GetParent()
		for p in xrange (notebook.GetPageCount()):
			if notebook.GetPage (p) is self:
				notebook.SetSelection (p)
				break
		return False
		
	def ValuesFromSettings (self, settings):
		'''Fill control values from a Trigger Stage in a SUMP device object.'''
		stage = self.stage
		self.arm_ctl.SetStringSelection (trigger_arm_settings [settings.trigger_level [stage]])
		self.mode_ctl.SetStringSelection (trigger_mode_settings [settings.trigger_serial [stage]])
		self.serial_channel_ctl.SetValue (str (settings.trigger_channel[stage]))
		
		trigger_mask = settings.trigger_mask [stage]
		for i, ctl in enumerate (self.mask_controls):
			ctl.SetValue (bool (trigger_mask & (1<<i)))
			
		trigger_values = settings.trigger_values [stage]
		for i, ctl in enumerate (self.value_controls):
			ctl.SetValue (bool (trigger_values & (1<<i)))
			
		self.capture_ctl.SetStringSelection (trigger_action_settings[settings.trigger_start[stage]])	# RadioBox
		sampling_rate = int (settings.clock_rate / settings.divider)
		self.delay_ctl.SetValue (str (
				self._delay_to_units (settings.trigger_delay[stage], settings.trigger_delay_unit[stage], sampling_rate) ))
		self.delay_unit_ctl.SetStringSelection (time_unit_settings[settings.trigger_delay_unit[stage]])
		
	def ValuesToSettings (self, settings):
		'''Update Trigger Stage settings in a repository from control values.'''
		stage = self.stage
		settings.trigger_level[stage] = trigger_arm_settings [self.arm_ctl.GetStringSelection()]
		settings.trigger_serial[stage] = trigger_mode_settings [self.mode_ctl.GetStringSelection()]
		settings.trigger_channel[stage] = int (self.serial_channel_ctl.GetValue())
		
		trigger_mask = 0
		for i, ctl in enumerate (self.mask_controls):
			trigger_mask |= ctl.IsChecked() << i
		settings.trigger_mask[stage] = trigger_mask
		
		trigger_values = 0
		for i, ctl in enumerate (self.value_controls):
			trigger_values |= ctl.IsChecked() << i
		settings.trigger_values[stage] = trigger_values
		
		settings.trigger_start[stage] = trigger_action_settings [self.capture_ctl.GetStringSelection()]
		settings.trigger_delay[stage] = self._delay_from_units (settings.clock_rate / settings.divider)
		print 'SumpTriggerPanel.ValuesToSettings trigger_delay[%d] %g' % (stage, settings.trigger_delay[stage])
		settings.trigger_delay_unit[stage] = time_unit_settings[self.delay_unit_ctl.GetStringSelection()]

#===========================================================
class SumpDialog (wx.Dialog):
	'''Dialog to enter controls for OpenLogic Sniffer.'''
	def __init__ (self, parent, settings=None):
		wx.Dialog.__init__ (self, parent, wx.ID_ANY, 'SUMP Device Settings')
		self.SetExtraStyle (wx.WS_EX_VALIDATE_RECURSIVELY)
		
		def labelled_ctl (sizer, label, ctl, sizer_ratio=0, sizer_flags=wx.EXPAND):
			hs = wx.BoxSizer (wx.HORIZONTAL)
			if label:
				hs.Add (wx.StaticText (self, wx.ID_ANY, label), 0, wx.ALIGN_CENTER_VERTICAL)
			hs.Add (ctl, 1, wx.EXPAND)
			sizer.Add (hs, sizer_ratio, sizer_flags)
			return ctl
			
		# Connection Settings
		self.port_ctl = wx.TextCtrl (self, -1, '/dev/ttyACM?')
		self.baud_ctl =  wx.ComboBox (self, wx.ID_ANY, '115200', choices=baud_rate_settings.labels, style=wx.CB_READONLY)
		self.connection_numbering_ctl = wx.RadioBox (self, wx.ID_ANY, 'Number Scheme '
				, choices=number_scheme_settings.labels )
		conbox = wx.StaticBox (self, wx.ID_ANY, 'Connection Settings')
		consizer = wx.StaticBoxSizer (conbox, wx.VERTICAL)
		labelled_ctl (consizer, 'Port   ', self.port_ctl)
		labelled_ctl (consizer, 'Baud ', self.baud_ctl)
		consizer.Add (self.connection_numbering_ctl, 0, 0)

		# Analyzer Settings
		self.sampling_clock_ctl = wx.RadioBox (self, wx.ID_ANY, 'Sampling Clock',
				choices=sampling_clock_settings.labels )
		self.sampling_rate_ctl = wx.ComboBox (self, wx.ID_ANY, '200MHz', choices=sampling_rate_settings.labels, style=wx.CB_READONLY)		
		self.recording_size_ctl = wx.ComboBox (self, wx.ID_ANY, '4K', choices=recording_size_settings.labels, style=wx.CB_READONLY)	
		anabox = wx.StaticBox (self, wx.ID_ANY, 'Analyzer Settings')
		anasizer = wx.StaticBoxSizer (anabox, wx.VERTICAL)
		anasizer.Add (self.sampling_clock_ctl, 0, 0)
				
		labelled_ctl (anasizer, 'Sampling Rate  ', self.sampling_rate_ctl)
		labelled_ctl (anasizer, 'Recording Size  ', self.recording_size_ctl)
		
		self.group_controls = [wx.CheckBox (self, -1) for i in xrange (4)]
		self.noise_filter_ctl = wx.CheckBox (self, -1)
		self.demux_ctl = wx.CheckBox (self, -1)
		self.rle_ctl = wx.CheckBox (self, -1)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		for label, ctl in zip (('0‥7', '8‥15', '16‥23', '24‥31'), self.group_controls):
			labelled_ctl (hs, label, ctl)
		labelled_ctl (anasizer, 'Channel Group   ', hs)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		labelled_ctl (hs, 'Filter ', self.noise_filter_ctl)
		hs.Add ((0,0), 1)
		labelled_ctl (hs, 'Demux ', self.demux_ctl)
		hs.Add ((0,0), 1)
		labelled_ctl (hs, 'RLE ', self.rle_ctl)
		anasizer.Add (hs, 0, wx.EXPAND)
		
		# Trigger Settings
		self.trigger_enable_ctl = wx.RadioBox (self, wx.ID_ANY, 'Enable', choices=trigger_enable_settings.labels)
		self.recording_ratio_ctl = wx.ComboBox (self, wx.ID_ANY, '0/100', choices=delay_ratio_settings.labels, style=wx.CB_READONLY)
		trigger_details = wx.Notebook (self, -1)
		self.trigger_pages = [SumpTriggerPanel (trigger_details, stage) for stage in xrange (4)]
		for p in self.trigger_pages:
			trigger_details.AddPage (p, 'Stage %d' % (p.stage,), p.stage==0)
			
		tribox = wx.StaticBox (self, wx.ID_ANY, 'Trigger Settings')
		trisizer = wx.StaticBoxSizer (tribox, wx.VERTICAL)
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add (self.trigger_enable_ctl, 0)
		hs.Add ((50,0), 1)
		labelled_ctl (hs, 'Pre/Post Ratio ', self.recording_ratio_ctl, 0, wx.ALIGN_CENTER_VERTICAL)
		trisizer.Add (hs, 0, 0)
		trisizer.Add (trigger_details, 1, wx.EXPAND|wx.TOP, 5)
		
		if settings is not None:
			self.ValuesFromSettings (settings)
		
		self._enable_valid_triggers (self.trigger_enable_ctl.GetStringSelection())
		
		# overall dialog layout ..
		top_sizer = wx.BoxSizer (wx.VERTICAL)	# top-level sizer for the dialog
		
		hs = wx.BoxSizer (wx.HORIZONTAL)
		hs.Add (consizer, 0, wx.EXPAND)
		hs.Add (anasizer, 0, wx.EXPAND|wx.LEFT, 10)
		top_sizer.Add (hs, 0, wx.EXPAND)
		top_sizer.Add (trisizer, 0, wx.EXPAND|wx.TOP, 10)
		
		capture_button = wx.Button (self, ID_CAPTURE, 'C&apture')
		capture_button.SetDefault()
		top_sizer.Add (capture_button, 0, wx.ALIGN_CENTER)
		top_sizer.Add (self.CreateButtonSizer (wx.OK|wx.CANCEL|wx.HELP), 0, wx.EXPAND|wx.ALIGN_CENTER)
		
		#~ wx.EVT_MENU (self, wx.ID_HELP,  self.OnHelp)
		wx.EVT_BUTTON (self, wx.ID_HELP,  self.OnHelp)
		capture_button.Bind (wx.EVT_BUTTON, self.OnCapture)
		self.trigger_enable_ctl.Bind (wx.EVT_RADIOBOX, self.OnTriggerEnableChange)
		
		self.SetSizer (top_sizer)
		self.SetInitialSize()

		
	def _enable_valid_triggers (self, enable_setting):
		'''Enable or disable trigger edit controls, depending on a trigger_enable value.'''
		if enable_setting == 'None':
			self.recording_ratio_ctl.Disable()
			for p in self.trigger_pages:
				p.Disable()
		elif enable_setting == 'Simple':
			self.recording_ratio_ctl.Enable()
			self.trigger_pages[0].Enable()
			for p in self.trigger_pages[1:]:
				p.Disable()
		elif enable_setting == 'Complex':
			self.recording_ratio_ctl.Enable()
			for p in self.trigger_pages:
				p.Enable()
				
	def _get_sample_rate (self):
		'''Return the sample rate called for by these settings.'''
		rate = sampling_rate_settings[self.sampling_rate_ctl.GetStringSelection()]
		if self.demux_ctl.GetValue():
			rate *= 2
		return rate
		
	def OnCapture (self, evt):
		self.EndModal (ID_CAPTURE)
		
	def OnHelp (self, evt):
		wx.MessageBox (helptext, 'SUMP Settings', style=wx.ICON_INFORMATION|wx.OK)
		#~ d = DocumentationWindow (None)
		#~ d.Show()
		
	def OnTriggerEnableChange (self, evt):
		self._enable_valid_triggers (evt.GetString())
		evt.Skip()
			
			
	def Validate (self):
		return wx.Dialog.Validate (self) and self._validate_trigger_delays()
		
	def _validate_trigger_delays (self):
		sample_rate = self._get_sample_rate()
		for tp in self.trigger_pages:
			if not tp._validate_delay (sample_rate):
				return False
		return True
		
		
	def ValuesFromSettings (self, settings):
		'''Fill control values from a repository.'''
		#~ self.port_ctl.SetValue (settings.portstr)	# `portstr` is deprecated; s/b `name` in future version
		#~ self.baud_ctl.SetStringSelection (baud_rate_settings [settings.baudrate])
		
		sampling_clock = (settings.external << 1) | settings.inverted
		sampling_rate = int (settings.clock_rate / settings.divider)
		
		#~ self.connection_numbering_ctl.SetStringSelection (number_scheme_settings[settings.number_scheme???])
		self.sampling_clock_ctl.SetStringSelection (sampling_clock_settings[sampling_clock])
		#~ self.sampling_rate_ctl.SetValue (sampling_rate_settings[int (sampling_rate)])
		self.sampling_rate_ctl.SetStringSelection (sampling_rate_settings[int (sampling_rate)])
		#~ self.recording_size_ctl.SetValue (recording_size_settings[settings.read_count])
		self.recording_size_ctl.SetStringSelection (recording_size_settings[settings.read_count])
		
		channel_groups = settings.channel_groups
		for ctl, mask in zip (self.group_controls, (1, 2, 4, 8)):
			ctl.SetValue (not (channel_groups & mask))
			
		self.noise_filter_ctl.SetValue (settings.filter)
		self.demux_ctl.SetValue (settings.demux)
		#~ self.rle_ctl.SetValue (settings.rle???)
		for v in delay_ratio_settings.values:
			if settings.delay_count >= v * settings.read_count:
				#~ self.recording_ratio_ctl.SetValue (delay_ratio_settings[v])
				self.recording_ratio_ctl.SetStringSelection (delay_ratio_settings[v])
				break
		self.trigger_enable_ctl.SetStringSelection (settings.trigger_enable)

		for p in self.trigger_pages:
			p.ValuesFromSettings (settings)
		
		
	def ValuesToSettings (self, settings):
		'''Create SUMP settings repository from control values.'''
		#~ settings.portstr = self.port_ctl.GetValue()
		#~ settings.baudrate = int (self.baud_ctl.GetStringSelection())
		sampling_clock = sampling_clock_settings[self.sampling_clock_ctl.GetStringSelection()]
		settings.external = sampling_clock >> 1
		settings.inverted = sampling_clock & 1
		sampling_rate = sampling_rate_settings [self.sampling_rate_ctl.GetValue()]
		settings.divider = int (settings.clock_rate / sampling_rate)
		settings.read_count = recording_size_settings [self.recording_size_ctl.GetValue()]
		settings.delay_count = int (settings.read_count * delay_ratio_settings [self.recording_ratio_ctl.GetValue()])
		
		channel_groups = 0
		for ctl, mask in zip (self.group_controls, (1, 2, 4, 8)):
			if ctl.GetValue():
				channel_groups |= mask
		settings.channel_groups = 0xF ^ channel_groups
		
		settings.filter = self.noise_filter_ctl.GetValue ()
		settings.demux = self.demux_ctl.GetValue ()
		
		trigger_enable = settings.trigger_enable = self.trigger_enable_ctl.GetStringSelection()
		if trigger_enable == 'None':
			for t in self.trigger_pages:
				t.trigger_mask = 0
				t.trigger_values = 0
				t.trigger_delay = 0
				t.trigger_level = 0
				t.trigger_channel = 0
				t.trigger_serial = False
				t.trigger_start = True
			
		elif trigger_enable == 'Simple':
			t = self.trigger_pages[0]
			t.ValuesToSettings (settings)
			t.trigger_level = 0
			t.trigger_start = True
			for t in self.trigger_pages[1:]:
				t.trigger_mask = 0
				t.trigger_values = 0
				t.trigger_delay = 0
				t.trigger_level = 0
				t.trigger_channel = 0
				t.trigger_serial = False
				t.trigger_start = False
				
		elif trigger_enable == 'Complex':
			for p in self.trigger_pages:
				p.ValuesToSettings (settings)
		else:
			settings_error ('ValuesToDevice: illegal trigger setting "%s"\n' % (trigger_enable,))
			
		return settings

#===========================================================
class DocumentationWindow (wx.Window):
	def __init__ (self, parent):
		wx.Window.__init__ (self, parent, -1)
		panel = wx.Panel (self, -1)
		#~ doc_ctl = wx.richtext.RichTextCtrl (panel, -1, "", style=wx.richtext.RE_READONLY|wx.richtext.RE_MULTILINE)
		#~ debug_output ('Created RichTextCtrl\n')
		#~ doc_ctl.AppendText (helptext)
		#~ debug_output ('Appended Text\n')
		doc_ctl = wx.TextCtrl (panel, -1, helptext, style=wx.TE_READONLY|wx.TE_MULTILINE)
		vs = wx.BoxSizer (wx.VERTICAL)
		vs.Add (panel, 1, wx.EXPAND)
		
		self.SetSizer (vs)
		self.SetInitialSize()


#===========================================================
class SimpleValidator (wx.PyValidator):
	'''Validators with defaults we can use.'''
	def Clone (self):
		return self.__class__()
		
	def TransferFromWindow (self):
		return True
		
	def TransferToWindow (self):
		return True
		
class PagedControlValidator (SimpleValidator):
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
			settings_error (error_message)
			# make sure the erroneous field is selected on the screen
			ctrl.SetFocus()
			ctrl.SetSelection (-1, -1)
			notebook = ctrl.GetGrandParent()
			if isinstance (notebook, wx.Notebook):
				# make sure the field's notebook page is selected
				page = ctrl.GetParent()
				for p in xrange (notebook.GetPageCount()):
					if notebook.GetPage (p) is page:
						notebook.SetSelection (p)
						break
		return result
		
		
class ChannelValidator (PagedControlValidator):
	def Validate (self, parent):
		return self.DoValidation (int, lambda v: 0 <= v <= 31, 'Channel value must be an integer from 0 to 31.')
		
class DelayValidator (PagedControlValidator):
	def Validate (self, parent):
		return self.DoValidation (float, lambda v: 0 <= v <= 65535, 'Delay value must be an integer from 0 to 65535.')
