#!/usr/bin/python -u
# -*- coding: utf-8 -*-


#--------------------------------------------------------------------------------
# Script to develop a modbus tcp communication to a ColorControl device with
# the Bornay aerogeneradores MPPT wind+.
# Author: Carlos Reyes Guerola
# date: 21/04/2017
# last update: 05/10/2017
# Version: 1.5.1
#---------------------------------------------------------------------------------
softwareVersion = '1.5.1'

from dbus.mainloop.glib import DBusGMainLoop
import time # Library to use delays
import gobject
from gobject import idle_add
import dbus
import dbus.service
import argparse
import inspect #import inspect library
import pprint #import pprint library
import os # Library to detect import libraries
import sys # system command library

#import the path of different libraries to use in modbus communication
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/pymodbus 1.3.2'))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/six-1.10.0'))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/importlib-1.0.4'))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/pyserial-3.3'))
import serial
import serial.rs485

#importing modbus complements for the rs485 communicaction
from pymodbus.exceptions import ModbusException, ParameterException
from pymodbus.pdu import ExceptionResponse, ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient# initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.exceptions import  ConnectionException
from pymodbus.exceptions import  NotImplementedException, ParameterException

#logging library config
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


# importing dbus complements
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
from vedbus import VeDbusService #VeDbusItemImportObject paths that are mandatory for services representing products

ccgx_rasp = (0,1) #0 for ccgx, 1 for rasp sets the system type
systemtype = "" #determines the system operation

#-----------------------------------------------------------------------------
# Sets the type of system (CCGX or rasp) to get permissions
# ENTRIES:
# systype: an integer who sets the system type
# RETURNS:
# the type of system
#-----------------------------------------------------------------------------
def system_type(systype):
	if systype == 0:
		return 'ccgx'
	else:
		return 'rasp'

# modbus class
class modbus():
	direction_sel = 1				# Id to connect
	instrument = ""					# Object who inizialises the modbus communication
	Port_sel =  "" 					# Serial port
	baud_sel = 57600				# Port speed
	bit_sel = 8					# Bits of the port
	parity_sel = 'N'				# Parity of the port
	stop_sel = 1					# Stop bits
	read_result = ""				# Reading exit
	delay = 1					# Delay between pols (in seconds)
	connected = 0					# If the port is connected or not
	conect_error = 0				# variable to controls the connection error


	#-----------------------------------------------------------------------------
	# Starts the modbus connection.
	# ENTRIES:
	#   -port : port selected
	#	-delay : delay between pols
	# RETURNS:
	# 	Nothing
	#-----------------------------------------------------------------------------
	def init(self, port, delay):
		try:
			self.instrument = ModbusClient(method='rtu', port=port, stopbits=self.stop_sel, bytesize=self.bit_sel,
					parity=self.parity_sel, baudrate=self.baud_sel, timeout=delay) #Modbus config
			self.instrument.connect() # Connect
			print("OK --> %s" % self.instrument.port)
			if systemtype == 'rasp':
				os.system("sudo chmod 666 %s" % port) # get permissions to open the port in a generic linux
			else:
				os.system("chmod a+rw %s" % port) # get permissions to open the port in a color control
			self.connected = 1
		except:
			sys.stderr.write("Error to open the port (%s)\n" % str(port)) # Except in error case
			self.conect_error = self.conect_error + 1
			self.connected = 0
		pass


	#-----------------------------------------------------------------------------
	# closes the modbus communication.
	# ENTRIES:
	# 	Nothing
	# RETURNS:
	# 	Nothing
	#-----------------------------------------------------------------------------
	def stop(self):
		self.instrument.close() # closes the port
		self.connected = 0
		self.conect_error = 0


	#-----------------------------------------------------------------------------
	# reads the value of a register.
	# ENTRIES:
	#   -register :register to read
	# RETURNS:
	#   returns the register value or a communication error
	#-----------------------------------------------------------------------------
	def read_register(self, register):
		try:
			print("Read holding register")
			self.read_result = self.instrument.read_holding_registers(address=register, count=1, unit=self.direction_sel)
			errors = 0
			print("Readed")
			return self.read_result.getRegister(0)
		except:
			return "error"


	#-----------------------------------------------------------------------------
	# reads a different registers
	# ENTRIES:
	#   -inicial_register : first register to read
	#   -number_registrers   : Number of registers to read
	# RETURNS:
	#    Returns a vector with the values of selected register or a communication error
	#-----------------------------------------------------------------------------
	def read_registers(self, inicial_register, number_registrers):
		try:
			print("Read holding registers")
			self.read_result = self.instrument.read_holding_registers(inicial_register, number_registrers, unit=self.direction_sel) # try to read
			print("Done")
			return self.read_result.registers # Return the register read
		except: # if it has an exception
			self.read_result = "error"
			return self.read_result # Returns erros to indicate an error comunication

# vbus class
class VBus():
	dbusservice = None	#dbus service variable
	value_modbus = "" 	#values read from bornay wind+ modbus
	args = ""		#extract parse argument
	init_on = 0		#variable to init the vebus service

	#-----------------------------------------------------------------------------
	# Initializes the different arguments to add.
	# ENTRIES:
	#   Nothing
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def parser_arguments(self):
		# Argument parsing
		parser = argparse.ArgumentParser(description='Wind+ with CCGX monitoring', add_help=False)
		parser.add_argument("-n", "--name", help="the D-Bus service you want me to claim",
			                    type=str, default="com.windcharger.bornay_ttyUSB0")
		parser.add_argument("-i", "--deviceinstance", help="the device instance you want me to be",
			                    type=str, default="0")
		parser.add_argument("-d", "--debug", help="set logging level to debug",
			                    action="store_true")
		parser.add_argument('-s', '--serial', default='/dev/ttyUSB0')

		self.args = parser.parse_args()
		print(self.args)
		# Init logging
		logging.basicConfig(level=(logging.DEBUG if self.args.debug else logging.INFO))
		logging.info(__file__ + " is starting up")
		logLevel = {0: 'NOTSET', 10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'}
		logging.info('Loglevel set to ' + logLevel[logging.getLogger().getEffectiveLevel()])

	#-----------------------------------------------------------------------------
	# Initializes the vbus protocol.
	# ENTRIES:
	#   Nothing
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def Init(self):
		try:
			DBusGMainLoop(set_as_default=True)
			self.dbusservice = VeDbusService('com.victronenergy.windcharger.bornay_ttyUSB0')
			self.__mandatory__()
			self.__objects_dbus__()
		except:
			print("Bornay wind+ has been created before")
			self.__mandatory__()

	#-----------------------------------------------------------------------------
	# Registers the mandatory instances
	# ENTRIES:
	#   Nothing
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def __mandatory__(self):
		try:
			logging.info("using device instance 0")

			# Create the management objects, as specified in the ccgx dbus-api document
			self.dbusservice.add_path('/Management/ProcessName', __file__)
			self.dbusservice.add_path('/Management/ProcessVersion', 'Version {} running on Python {}'.format(softwareVersion, sys.version))
			self.dbusservice.add_path('/Management/Connection', 'ModBus RTU')

			# Create the mandatory objects
			self.dbusservice.add_path('/DeviceInstance', 0)
			self.dbusservice.add_path('/ProductId', 0)
			self.dbusservice.add_path('/ProductName', 'Bornay Wind+ MPPT')
			self.dbusservice.add_path('/FirmwareVersion', softwareVersion)
			self.dbusservice.add_path('/HardwareVersion', 1.01)
			self.dbusservice.add_path('/Connected', 1)
		except:
			print("Mandatory Bornay wind+ has been created before")
			self.__objects_dbus__()

	#-----------------------------------------------------------------------------
	# Creates the different registers to save.
	# ENTRIES:
	#   Nothing
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def __objects_dbus__(self):
		try:
			# Create all the objects that we want to export to the dbus
			# All are initialized with the same value 0
			self.dbusservice.add_path('/Mppt/StatusMEF', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/RefMEF', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/BatPowerLastMin', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/BatPowerLastHour', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/BreakerPowerLastMin', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/WindSpeedLastMin', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/WindSpeedLastHour', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/Phase', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/SinkTemp', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/BoxTemp', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ElevatedVoltaje', 0, writeable=True)
			self.dbusservice.add_path('/Flags/Extrem', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ExternSupply', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ElevatedWind', 0, writeable=True)
			self.dbusservice.add_path('/Flags/FanState', 0, writeable=True)
			self.dbusservice.add_path('/Flags/EmergencyButton', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/RPM', 0, writeable=True)
			self.dbusservice.add_path('/History/Overall/MaxRPM', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/Dutty', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/WindSpeed', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/VDC', 0, writeable=True)
			self.dbusservice.add_path('/Dc/0/Current', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/IBrk', 0, writeable=True)
			self.dbusservice.add_path('/Dc/0/Power', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/AvailablePower', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/Stop', 0, writeable=True)
			self.dbusservice.add_path('/Dc/0/Voltage', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/ChargerState', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/StimatedWind', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ChargedBattery', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/AbsortionTime', 0, writeable=True)
		except:
			print("Bornay wind+ objects has been created before")

	#-----------------------------------------------------------------------------
	# Update the different registers to save in dbus.
	# ENTRIES:
	#   -modbus_values: Vector who contains the bornay modbus values
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def update_modbus_values(self):
		self.dbusservice['/Mppt/StatusMEF'] = self.value_modbus[0]
		self.dbusservice['/Mppt/RefMEF'] = self.value_modbus[1]
		self.dbusservice['/Turbine/BatPowerLastMin'] = self.value_modbus[2]
		self.dbusservice['/Turbine/BatPowerLastHour'] = self.value_modbus[3]
		self.dbusservice['/Turbine/BreakerPowerLastMin'] = self.value_modbus[4]
		self.dbusservice['/Turbine/WindSpeedLastMin'] = self.value_modbus[5]
		self.dbusservice['/Turbine/WindSpeedLastHour'] = self.value_modbus[6]
		self.dbusservice['/Mppt/Phase'] = self.value_modbus[7]
		self.dbusservice['/Mppt/SinkTemp'] = (self.value_modbus[8]/10)
		self.dbusservice['/Mppt/BoxTemp'] = (self.value_modbus[9]/10)
		self.dbusservice['/Flags/ElevatedVoltaje'] = self.value_modbus[10]
		self.dbusservice['/Flags/Extrem'] = self.value_modbus[11]
		self.dbusservice['/Flags/ExternSupply'] = self.value_modbus[12]
		self.dbusservice['/Flags/ElevatedWind'] = self.value_modbus[13]
		self.dbusservice['/Flags/FanState'] = self.value_modbus[14]
		self.dbusservice['/Flags/EmergencyButton'] = self.value_modbus[15]
		self.dbusservice['/Turbine/RPM'] = self.value_modbus[16]
		self.dbusservice['/History/Overall/MaxRPM'] = self.value_modbus[17]
		self.dbusservice['/Mppt/Dutty'] = self.value_modbus[18]
		self.dbusservice['/Turbine/WindSpeed'] = (self.value_modbus[19]/100)
		self.dbusservice['/Turbine/VDC'] = (self.value_modbus[20]/10)
		self.dbusservice['/Dc/0/Current'] = (self.value_modbus[21]/10)
		self.dbusservice['/Turbine/IBrk'] = (self.value_modbus[22]/10)
		self.dbusservice['/Dc/0/Power'] = self.value_modbus[23]
		self.dbusservice['/Turbine/AvailablePower'] = self.value_modbus[24]
		self.dbusservice['/Turbine/Stop'] = self.value_modbus[25]
		self.dbusservice['/Dc/0/Voltage'] = (self.value_modbus[26]/10)
		self.dbusservice['/Mppt/ChargerState'] = self.value_modbus[27]
		self.dbusservice['/Turbine/StimatedWind'] = (self.value_modbus[28]/10)
		self.dbusservice['/Flags/ChargedBattery'] = self.value_modbus[29]
		self.dbusservice['/Mppt/AbsortionTime'] = self.value_modbus[30]
		pass


# -----------------------------------------------------------------------------
# Main module
# -----------------------------------------------------------------------------
if __name__ == '__main__':
	systemtype = system_type(ccgx_rasp[1]) #sets a ccgx system
	#init the different class of the script
	s = modbus() # starts modbus class
	ve = VBus() #init vbus class
	ve.parser_arguments() #saves the parser arguments
	s.Port_sel = ve.args.serial #gets the serial port argument
	#config the serial comunication
	s.direction_sel = 1
	s.baud_sel = 57600
	s.bit_sel = 8
	s.parity_sel = 'N'
	s.stop_sel = 1
	s.delay = 1
	#init bornay modbus
	s.init(s.Port_sel, s.delay)
	#main loop
	while 1:
		if s.connected == 0 and s.conect_error <=2: #if the port is not connected, try another time to connect
			s.init(s.Port_sel, s.delay)
			if s.conect_error == 2: #if the error repeats one more time, stops the script
				s.stop()
				sys.exit("Connection lost")
		else:
			s.read_result = s.read_registers(5000,31) #read modbus data
			print("Exit %s with %d errors" % (s.read_result, s.conect_error))
			if s.read_result == "error":
				s.conect_error = s.conect_error + 1
				if s.conect_error == 2: #if we have a lot of errors, stops the script
					s.conect_error = 0
					s.connected = 0
					s.stop()
					sys.exit("Connection lost")
			else: #in case of no error, transfer the bornay modbus data to dbus protocol
				if ve.init_on == 0:
					ve.Init() #init the vebus config and directories
					ve.init_on = 1
				s.conect_error = 0 #sets the error count to zero
				ve.value_modbus = s.read_result #transfer modbus data read to ve variable
				ve.update_modbus_values()
				mainloop = gobject.MainLoop()
				#mainloop.run()
				time.sleep(s.delay) #delay to not collapse the dbus
