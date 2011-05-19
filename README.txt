pyLogicSniffer is a client for the Open Bench Logic Sniffer 
<http://gadgetforge.gadgetfactory.net/gf/project/butterflylogic/>

pyLogicSniffer is written in Python, using the wxPython GUI package.


Dependencies:

Python 2.x	<http://www.python.org/>
wxPython		<http://www.wxpython.org/>
NumPy		<http://numpy.scipy.org/>
pySerial		<http://pyserial.sourceforge.net/>


Modules:

analyzer_tool_spi.py		SPI Trace Analyzer plugin
analyzer_tool_twi.py		TWI (I2C) Trace Analyzer plugin
analyzer_tool_uart.py		Serial UART Trace Analyzer plugin
analyzer_tools.py		Common utilities for Trace Analyzer plugin modules
logic_sniffer_classes.py	Common classes for logic_sniffer
logic_sniffer_dialogs.py	Common dialog classes for logic_sniffer
logic_sniffer.py			pyLogicSniffer main script
logic_sniffer_save.py		Functions to save trace data
sump.py				Classes to control SUMP device
sump_config_file.py		Functions to save and restore SUMP device settings
sump_settings.py		Dialogs to manage SUMP device settings


License:

    pyLogicSniffer is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pyLogicSniffer is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with pyLogicSniffer, in the file COPYING.txt.  
    If not, see <http://www.gnu.org/licenses/>.
