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

global server
global ip

def GetCurrentTemperature():
        return random.uniform(70, 95)

def GetCurrentHumidity():
        return random.uniform(80, 100)

def DataSimulationThread(update_interval, e):
	print 'Data simulation thread started'
	
	# Allocate a client	
	client = ModbusTcpClient(ip)
	
	# Scan the data source
	value = 0
	while True:
		if not e.isSet():
			time.sleep(1)			

			#TODO: Write temperature to register			
			#TODO: Write temperature to display			
			#client.write_registers(0, GetCurrentTemperature())
			#result = client.read_registers(0, 1)
			#print 'Register 0 is currently ' + str(result[0])
			print 'Nothing to see here'

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
	server = ModbusTcpServer(context, identity=identity, address=(ip, 502))
	print 'Server started'
	server.serve_forever(0.1)
	print 'Server stopped'


if __name__ == "__main__":
	global server
	global ip
	print "=== Modbus Device ==="
	parser = argparse.ArgumentParser(description='Modbus server')
	parser.add_argument('ip',  default='localhost', help='IP adress of modbus server')
	args = parser.parse_args()
	ip = args.ip
	
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
