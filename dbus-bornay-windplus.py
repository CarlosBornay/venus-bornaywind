#!/usr/bin/python -u
# -*- coding: utf-8 -*-


#--------------------------------------------------------------------------------
# Script to develop a modbus tcp communication to a ColorControl device with
# the Bornay aerogeneradores MPPT wind+.
# Author: Carlos Reyes Guerola
# date: 21/04/2017
# last update: 10/04/2018
# Version: 1.5.8
#---------------------------------------------------------------------------------
__author__ = "Carlos Reyes Guerola"
__copyright__ = "Copyright 2018, Bornay aerogeneradores S.L.U"
__credits__ = ["CRG@18"]
__license__ = "Bornay aerogeneradores S.L.U"
__version__ = "1.5.7"
__maintainer__ = __author__
__email__ = "bornay@bornay.com"


import time # Library to use delays
from argparse import ArgumentParser
import os # Library to detect import libraries
import sys # system command library
import serial
import serial.rs485
from dbus.mainloop.glib import DBusGMainLoop

#importing modbus complements for the rs485 communicaction
from pymodbus.client.sync import ModbusSerialClient as ModbusClient# initialize a serial RTU client instance

#logging library config
import logging
logging.basicConfig()
log = logging.getLogger()
#log.setLevel(logging.DEBUG) #Uncomment for debug


# importing dbus complements
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
from vedbus import VeDbusService #VeDbusItemImportObject paths that are mandatory for services representing products

# modbus class
class modbus():
	def __init__(self):
		self.direction_sel = 1		# Id to connect
		self.instrument = ""		# Object who inizialises the modbus communication
		self.Port_sel =  "" 		# Serial port
		self.baud_sel = 57600		# Port speed
		self.bit_sel = 8			# Bits of the port
		self.parity_sel = 'N'		# Parity of the port
		self.stop_sel = 1			# Stop bits
		self.read_result = ""		# Reading exit
		self.delay = 1				# Delay between pols (in seconds)
		self.connected = 0			# If the port is connected or not
		self.connect_error = 0		# variable to controls the connection error


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
			log.debug("OK --> %s" % self.instrument.port)
			self.connected = 1
		except:
			sys.stderr.write("Error to open the port (%s)\n" % str(port)) # Except in error case
			self.connect_error = self.connect_error + 1
			self.connected = 0

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
		self.connect_error = 0


	#-----------------------------------------------------------------------------
	# reads the value of a register.
	# ENTRIES:
	#   -register :register to read
	# RETURNS:
	#   returns the register value or a communication error
	#-----------------------------------------------------------------------------
	def read_register(self, register):
		try:
			log.debug("Read holding register")
			self.read_result = self.instrument.read_holding_registers(address=register, count=1, unit=self.direction_sel)
			errors = 0
			log.debug("Readed")
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
			log.debug("Read holding registers")
			self.read_result = self.instrument.read_holding_registers(inicial_register, number_registrers, unit=self.direction_sel) # try to read
			log.debug("Done")
			return self.read_result.registers # Return the register read
		except: # if it has an exception
			self.read_result = "error"
			return self.read_result # Returns erros to indicate an error comunication

# vbus class
class VBus():
	def __init__(self):
		self.dbusservice = None	#dbus service variable
		self.args = ""		#extract parse argument
		self.init_on = 0		#variable to init the vebus service

	#-----------------------------------------------------------------------------
	# Initializes the different arguments to add.
	# ENTRIES:
	#   Nothing
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def parser_arguments(self):
		# Argument parsing
		parser = ArgumentParser(description='Wind+ with CCGX monitoring', add_help=True)
		parser.add_argument("-n", "--name", help="the D-Bus service you want me to claim",
			                    type=str, default="com.windcharger.bornay_ttyUSB0")
		parser.add_argument("-i", "--deviceinstance", help="the device instance you want me to be",
			                    type=str, default="0")
		parser.add_argument("-d", "--debug", help="set logging level to debug",
			                    action="store_true")
		parser.add_argument('-s', '--serial', default='/dev/ttyUSB0')

		self.args = parser.parse_args()
		log.info(self.args)
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
			serial = os.path.basename(self.args.serial)
			self.dbusservice = VeDbusService('com.victronenergy.windcharger.bornay_' + serial)
			self.__mandatory__()
			self.__objects_dbus__()
		except:
			log.warn("Bornay wind+ has been created before")
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
			self.dbusservice.add_path('/Management/ProcessVersion', 'Version {} running on Python {}'.format(__version__, sys.version))
			self.dbusservice.add_path('/Management/Connection', 'ModBus RTU')

			# Create the mandatory objects
			self.dbusservice.add_path('/DeviceInstance', 0)
			self.dbusservice.add_path('/ProductId', 0)
			self.dbusservice.add_path('/ProductName', 'Bornay Wind+ MPPT')
			self.dbusservice.add_path('/FirmwareVersion', __version__)
			self.dbusservice.add_path('/HardwareVersion', 1.01)
			self.dbusservice.add_path('/Connected', 1)
		except:
			log.warn("Mandatory Bornay wind+ has been created before")
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
			self.dbusservice.add_path('/Flags/ElevatedVoltage', 0, writeable=True)
			self.dbusservice.add_path('/Flags/Extrem', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ExternSupply', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ElevatedWind', 0, writeable=True)
			self.dbusservice.add_path('/Flags/FanState', 0, writeable=True)
			self.dbusservice.add_path('/Flags/EmergencyButton', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/RPM', 0, writeable=True)
			self.dbusservice.add_path('/History/Overall/MaxRPM', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/DuttyCycle', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/WindSpeed', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/VDC', 0, writeable=True)
			self.dbusservice.add_path('/Dc/0/Current', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/IBrk', 0, writeable=True)
			self.dbusservice.add_path('/Dc/0/Power', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/AvailablePower', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/Stop', 0, writeable=True)
			self.dbusservice.add_path('/Dc/0/Voltage', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/ChargerState', 0, writeable=True)
			self.dbusservice.add_path('/Turbine/EstimatedWind', 0, writeable=True)
			self.dbusservice.add_path('/Flags/ChargedBattery', 0, writeable=True)
			self.dbusservice.add_path('/Mppt/AbsortionTime', 0, writeable=True)
		except:
			log.warn("Bornay wind+ objects has been created before")

	#-----------------------------------------------------------------------------
	# Update the different registers to save in dbus.
	# ENTRIES:
	#   -modbus_values: Vector who contains the bornay modbus values
	# RETURNS:
	#   Nothing
	#-----------------------------------------------------------------------------
	def update_modbus_values(self, value_modbus):
		self.dbusservice['/Mppt/StatusMEF'] = value_modbus[0]
		self.dbusservice['/Mppt/RefMEF'] = value_modbus[1]
		self.dbusservice['/Turbine/BatPowerLastMin'] = value_modbus[2]
		self.dbusservice['/Turbine/BatPowerLastHour'] = value_modbus[3]
		self.dbusservice['/Turbine/BreakerPowerLastMin'] = value_modbus[4]
		self.dbusservice['/Turbine/WindSpeedLastMin'] = value_modbus[5]
		self.dbusservice['/Turbine/WindSpeedLastHour'] = value_modbus[6]
		self.dbusservice['/Mppt/Phase'] = value_modbus[7]
		self.dbusservice['/Mppt/SinkTemp'] = (value_modbus[8]/10)
		self.dbusservice['/Mppt/BoxTemp'] = (value_modbus[9]/10)
		self.dbusservice['/Flags/ElevatedVoltage'] = value_modbus[10]
		self.dbusservice['/Flags/Extrem'] = value_modbus[11]
		self.dbusservice['/Flags/ExternSupply'] = value_modbus[12]
		self.dbusservice['/Flags/ElevatedWind'] = value_modbus[13]
		self.dbusservice['/Flags/FanState'] = value_modbus[14]
		self.dbusservice['/Flags/EmergencyButton'] = value_modbus[15]
		self.dbusservice['/Turbine/RPM'] = value_modbus[16]
		self.dbusservice['/History/Overall/MaxRPM'] = value_modbus[17]
		self.dbusservice['/Mppt/DuttyCycle'] = value_modbus[18]
		self.dbusservice['/Turbine/WindSpeed'] = (value_modbus[19]/100)
		self.dbusservice['/Turbine/VDC'] = (value_modbus[20]/10)
		self.dbusservice['/Dc/0/Current'] = (value_modbus[21]/10)
		self.dbusservice['/Turbine/IBrk'] = (value_modbus[22]/10)
		self.dbusservice['/Dc/0/Power'] = value_modbus[23]
		self.dbusservice['/Turbine/AvailablePower'] = value_modbus[24]
		self.dbusservice['/Turbine/Stop'] = value_modbus[25]
		self.dbusservice['/Dc/0/Voltage'] = (value_modbus[26]/10)
		self.dbusservice['/Mppt/ChargerState'] = value_modbus[27]
		self.dbusservice['/Turbine/EstimatedWind'] = (value_modbus[28]/10)
		self.dbusservice['/Flags/ChargedBattery'] = value_modbus[29]
		self.dbusservice['/Mppt/AbsortionTime'] = value_modbus[30]


# -----------------------------------------------------------------------------
# Main module
# -----------------------------------------------------------------------------
if __name__ == '__main__':
	log.info("dbus-bornay-windplus app") #Prints all info of app
	log.info(__author__)
	log.info(__copyright__)
	log.info(__credits__)
	log.info(__license__)
	log.info(__version__)
	log.info(__maintainer__)
	log.info(__email__)

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
	while True:
		if s.connected == 0 and s.connect_error <=2: #if the port is not connected, try another time to connect
			s.init(s.Port_sel, s.delay)
			if s.connect_error == 2: #if the error repeats one more time, stops the script
				s.stop()
				sys.exit("Connection lost")
		else:
			s.read_result = s.read_registers(5000,31) #read modbus data
			log.debug("Exit %s with %d errors" % (s.read_result, s.connect_error))
			if s.read_result == "error":
				s.connect_error = s.connect_error + 1
				if s.connect_error == 2: #if we have a lot of errors, stops the script
					s.connect_error = 0
					s.connected = 0
					s.stop()
					sys.exit("Connection lost")
			else: #in case of no error, transfer the bornay modbus data to dbus protocol
				if ve.init_on == 0:
					ve.Init() #init the vebus config and directories
					ve.init_on = 1
				s.connect_error = 0 #sets the error count to zero
				value_modbus = s.read_result #transfer modbus data read to ve variable
				ve.update_modbus_values(value_modbus)
		time.sleep(s.delay) #delay to not collapse the dbus
