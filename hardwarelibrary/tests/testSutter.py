import env # modifies path
import unittest
import time
from threading import Thread, Lock
from struct import *

import pyftdi.serialext
import pyftdi.ftdi 
from pyftdi.ftdi import Ftdi

from hardwarelibrary.motion.sutterdevice import SutterDevice, SutterDebugSerialPort 
from hardwarelibrary.communication.serialport import SerialPort


# class TestSutterSerialPortBase:
#     port = None

#     def testCreate(self):
#         self.assertIsNotNone(self.port)

#     def testCantReopen(self):
#         self.assertIsNotNone(self.port)
#         self.assertTrue(self.port.isOpen)
#         with self.assertRaises(Exception) as context:
#             self.port.open()

#     def testCloseReopen(self):
#         self.assertIsNotNone(self.port)
#         self.assertTrue(self.port.isOpen)
#         self.port.close()
#         self.port.open()

#     def testCloseTwice(self):
#         self.assertIsNotNone(self.port)
#         self.assertTrue(self.port.isOpen)
#         self.port.close()
#         self.port.close()

#     def testCantReadEmptyPort(self):
#         self.assertIsNotNone(self.port)
#         self.assertTrue(self.port.isOpen)
#         with self.assertRaises(CommunicationReadTimeout) as context:
#             self.port.readString()

#     def testMove(self):
#         self.assertIsNotNone(self.port)
#         payload = bytearray('m',encoding='utf-8')
#         payload.extend(pack("<lll",1,2,3))
#         self.port.writeData(payload)
#         self.assertTrue(self.port.readData(length=1) == b'\r')

#     def testMoveGet(self):
#         self.assertIsNotNone(self.port)
#         payload = bytearray('m',encoding='utf-8')
#         payload.extend(pack("<lll",1,2,3))
#         self.port.writeData(payload)
#         self.assertTrue(self.port.readData(length=1) == b'\r')

#         payload = bytearray('c',encoding='utf-8')
#         self.port.writeData(payload)
#         data = self.port.readData(length=4*3)
#         (x,y,z) = unpack("<lll", data)
#         self.assertTrue( x == 1)
#         self.assertTrue( y == 2)
#         self.assertTrue( z == 3)

# class TestSutterDebugSerialPort(TestSutterSerialPortBase, unittest.TestCase):

#     def setUp(self):
#         self.port = SutterDebugSerialPort()
#         self.assertIsNotNone(self.port)
#         self.port.open()

#     def tearDown(self):
#         self.port.close()


class TestSutterDevice(unittest.TestCase):
    def setUp(self):
            # pyftdi.ftdi.Ftdi.add_custom_product(vid=4930, pid=1, pidname='Sutter')
        self.device = SutterDevice()
        self.assertIsNotNone(self.device)
        self.device.doInitializeDevice()

    def tearDown(self):
        self.device.doShutdownDevice()
        self.device = None

    # def testFTDIPortsAddCustomManully(self):
        
    #     ports = SerialPort.ftdiPorts()
    #     print(ports)

    # def testFTDIPorts(self):

    #     ports = SerialPort.matchPorts()
    #     print(ports)

    # def testSutterSerial(self):
    #     port = SerialPort.matchAnyPort(idVendor=4930, idProduct=1, serialNumber=None)
    #     print(port)

    def testDevicePosition(self):
        self.device.home()

    def testDevicePosition(self):
        (x, y, z) = self.device.positionInMicrosteps()
        self.assertIsNotNone(x)
        self.assertIsNotNone(y)
        self.assertIsNotNone(z)
        self.assertTrue(x>=0)
        self.assertTrue(y>=0)
        self.assertTrue(z>=0)
    def testDeviceMove(self):
        destination = (1,2,3)
        self.device.moveTo( destination )

        (x,y,z) = self.device.position()
        self.assertTrue(x==destination[0])
        self.assertTrue(y==destination[1])
        self.assertTrue(z==destination[2])

    def testDeviceMoveBy(self):
        (xo,yo,zo) = self.device.position()

        self.device.moveBy( (10,20,30) )

        (x,y,z) = self.device.position()
        self.assertTrue(x-x0 == 10)
        self.assertTrue(y-y0 == 20)
        self.assertTrue(z-z0 == 30)

if __name__ == '__main__':
    unittest.main()
