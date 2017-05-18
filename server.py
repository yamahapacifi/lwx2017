import time
import argparse
import sys, traceback
import threading
import pymodbus
import random

from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.server.sync import ModbusTcpServer

from sense_hat import SenseHat

global server
global cip
global sip

def C2F(c):
        return c*9/5 + 32

def Flt2Disp(f):
        return "{0:.2f}".format(f)

def DataSimulationThread(update_interval, e):
	print 'Data simulation thread started'

	# Allocate Sense HAT interface
	sense = SenseHat()

	# FIXME: Adjust rotation for my desktop
	sense.set_rotation(180)	
	
	# Allocate a client	
	client = ModbusTcpClient(cip)
	
	# Scan the data source
	value = 0
	while True:
		if not e.isSet():
			time.sleep(1)

			# Retrieve temp
			tempInF = C2F(sense.get_temperature())			
			
			# Write temp to pymodbus register
			client.write_register(0, tempInF)

			# Retrieve humidity
			humidity = sense.get_humidity ()

			# Write humidity to pymodbus register
			client.write_register(1, humidity)

                        # Display temp on the LED matrix
			tempStrInF = Flt2Disp(tempInF)
			sense.show_message(tempStrInF)

                        # Log our values
			print 'Current temperature is ' + tempStrInF
			print 'Current humidity is ' + str(humidity)

		else:
			break
	client.close()
	print 'Data simulation thread stopped'


def ServerThread(e):
	global server
	
	# Initialize your data store
	store = ModbusSlaveContext(
		di = ModbusSequentialDataBlock(0, [17]*100),
		co = ModbusSequentialDataBlock(0, [17]*100),
		hr = ModbusSequentialDataBlock(0, [17]*100),
		ir = ModbusSequentialDataBlock(0, [17]*100))
	context = ModbusServerContext(slaves=store, single=True)
	 
	# Initialize the server information
	identity = ModbusDeviceIdentification()
	identity.VendorName  = 'Pymodbus'
	identity.ProductCode = 'PM'
	identity.VendorUrl   = 'http://github.com/bashwork/pymodbus/'
	identity.ProductName = 'Pymodbus Server'
	identity.ModelName   = 'Pymodbus Server'
	identity.MajorMinorRevision = '1.0'

	# Run the server 
	server = ModbusTcpServer(context, identity=identity, address=(sip, 502))
	print 'Server started'
	server.serve_forever(0.1)
	print 'Server stopped'


if __name__ == "__main__":
	global server
	global cip
	global sip
	print "=== Modbus Device ==="
	parser = argparse.ArgumentParser(description='Modbus server')
	parser.add_argument('cip', nargs='?', default='localhost', help='IP adress of modbus client')
	parser.add_argument('sip', nargs='?', default='0.0.0.0', help='IP adress of modbus server')
	args = parser.parse_args()
	sip = args.sip
	cip = args.cip
	
	e_exit = threading.Event()
	
	thServer = threading.Thread(name='ServerThread', target=ServerThread, args=(e_exit,))
	thDataSimulation = threading.Thread(name='DataSimulationThread', target=DataSimulationThread, args=(1, e_exit,))
	thServer.start()
	time.sleep(1)
	
	# Start clients
	thDataSimulation.start()	

	# Wait for keyboard interrupt
	try:
                while True:
                        time.sleep(1)
	except KeyboardInterrupt:
		print "Keyboard interrupt acknowledged, stopping program."
	except Exception:
		traceback.print_exc(file=sys.stdout)	
	
	
	# Set stop event for clients
	e_exit.set()

	# Wait until all clients stop
	# or thDataSimulation.isAlive()
	while thDataSimulation.isAlive():
		time.sleep(0.01)
	
	# Shutdown server
	server.shutdown()

	# Wait until server shutdown
	while thServer.isAlive():
		time.sleep(0.01)
		
	# Stop the program
	print 'Done'
	sys.exit(0)
