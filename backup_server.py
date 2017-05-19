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
global cip
global sip

def C2F(c):
        return c*9/5 + 32


def Flt2Disp(f):
        return "{0:.2f}".format(f)


def LEDMatrixDisplayThread(update_interval, e):
        global tempInF
        global lock
        print 'LED matrix display thread started'
        while True:
		if not e.isSet():
                        # Grab the latest value
                        temp = 0
                        with lock:
                                temp = tempInF
                        print 'Temp: ' + Flt2Disp(tempInF) + ' degrees F'
                        time.sleep(0.5)
                else:
                        break
        print 'LED matrix display thread stopped'


def doIo(client):
        global tempInF
        with lock:                        
                # Retrieve temp
                tempInF = random.uniform(60, 95)
                                
                # Retrieve humidity
                humidity = random.uniform(30, 100)

                # Get orientation
                pitch = random.uniform(0,360)
                roll = random.uniform(0, 360)
                yaw = random.uniform(0, 360)

                # Enable the compass (disables the gyroscope)
                north = random.uniform(0, 360)

                # Write temp to pymodbus register
                client.write_register(0, tempInF)
                        
                # Write humidity to pymodbus register
                client.write_register(1, humidity)

                # Write pitch, roll, and yaw to pymodbus registers
                client.write_register(2, pitch)
                client.write_register(3, roll)
                client.write_register(4, yaw)                                

                # Write compass to pymodbus register
                client.write_register(5, north)


def DataCollectionThread(update_interval, e):
        global lock
	print 'Data collection thread started'
	
	# Allocate a client	
	client = ModbusTcpClient(cip)
	
	# Scan the data source
	value = 0
	while True:
		if not e.isSet():
                        # Give some time back to the system
                        time.sleep(0.3)
                        doIo(client)                        
		else:
			break
		
	client.close()
	print 'Data collection thread stopped'
	

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
	global tempInF
	global lock

        # Allocate globals
        tempInF = 0
        lock = threading.Lock()
	
	print "=== Modbus Device ==="
	parser = argparse.ArgumentParser(description='Modbus server')
	parser.add_argument('cip', nargs='?', default='localhost', help='IP adress of modbus client')
	parser.add_argument('sip', nargs='?', default='0.0.0.0', help='IP adress of modbus server')
	args = parser.parse_args()
	sip = args.sip
	cip = args.cip
	
	e_exit = threading.Event()
	
	thServer = threading.Thread(name='ServerThread', target=ServerThread, args=(e_exit,))
	thDataCollection = threading.Thread(name='DataCollectionThread', target=DataCollectionThread, args=(1, e_exit,))
	thLEDMatrixDisplay = threading.Thread(name='LEDMatrixDisplayThread', target=LEDMatrixDisplayThread, args=(1, e_exit,))
	thServer.start()
	time.sleep(1)
	
	# Start clients
	thDataCollection.start()
	thLEDMatrixDisplay.start()

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

	# Wait for data thread to stop
	while thDataCollection.isAlive():
		time.sleep(0.1)

        # Wait for LED Matrix Display thread to stop
	while thLEDMatrixDisplay.isAlive():
                time.sleep(0.1)
	
	# Shutdown server
	server.shutdown()

	# Wait until server shutdown
	while thServer.isAlive():
		time.sleep(0.01)
		
	# Stop the program
	print 'Done'
	sys.exit(0)
