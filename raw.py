import log_utils # utils.log_utils
import socket
import selectors
import struct
import binascii
import threading
import time

from ethernet import *

log = log_utils.logging_init(__file__) # utils.log_utils.logging_init(__file__)

class setRaw(threading.Thread):
    # Broadcast: Destination address = 0 
    def __init__(self, interface, destinationAdd, flowCtrl, rawData):
        threading.Thread.__init__(self)
        self.preamble = b'\x55\x55\x55\x55\x55\x55\x55'  #55555555555555
        self.sof = b'\xD5'
        self.sourceAdd = b'\x00\x00\x00\x00\x00\x01' # 主控
        self.packageIndex = b'\x63'
        
        rawData = binascii.unhexlify(rawData)
        dataLen = len(rawData)
        if dataLen > 1480:
            print('data length is over MTU!!')
            return
        
        # count CRC
        CRC = 0
        for i in range(len(self.preamble)):
            CRC += self.preamble[i]
            
        for i in range(dataLen):
            CRC += rawData[i]
            
        for i in range(len(self.sourceAdd)):
            CRC += self.sourceAdd[i]
        
        for i in range(len(destinationAdd)):
            CRC += destinationAdd[i]
        CRC += self.sof[0]
        CRC += flowCtrl[0]
        CRC += self.packageIndex[0]
        CRC += dataLen
        
        # set self parameter
        self.dataLen = dataLen
        self.interface = interface
        self.destinationAdd = destinationAdd
        self.flowCtrl = flowCtrl
        self.rawData = rawData
        self.CRC = CRC
        '''
        print('preamble:', self.preamble)
        print('sof:', self.sof)
        print('sourceAdd:', self.sourceAdd)
        print('interface:', interface)
        print('destinationAdd:', self.destinationAdd)
        print('flowCtrl:', self.flowCtrl)
        print('rawData:', self.rawData)
        print('CRC:', self.CRC)
        print('dataLen:', self.dataLen)
        '''
    
    def run(self):
        with socket.socket(socket.AF_PACKET, socket.SOCK_RAW) as client_socket:
            # Bind an interface
            client_socket.bind((self.interface, 0))
            # Send a frame
            client_socket.sendall(
                # Pack in network byte order (frame)
                struct.pack('!6s6ssHs' + str(self.dataLen) + 's16s',
                            #eui48_to_bytes(self.destinationAdd),
                            self.destinationAdd,
                            self.sourceAdd,
                            self.packageIndex,
                            self.dataLen, # number of data byte
                            self.flowCtrl,
                            self.rawData,
                            b'\xcc\xcc\xcc\xcc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'))  
                            #self.CRC.to_bytes(4, 'big')))  
            print('Sent!')
    '''    
    def receiveSocket(self):
        # receive ACK
        # Create a layer 2 raw socket that receive any Ethernet frames (= ETH_P_ALL)
        with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as server_socket:
            # Bind the interface
            server_socket.bind((self.interface, 0))
            with selectors.DefaultSelector() as selector:
                # Resister the socket for selection, monitoring it for I/O events
                selector.register(server_socket.fileno(), selectors.EVENT_READ)
                while True:
                    if stopThreads:
                        break
                    # Wait until the socket become readable
                    ready = selector.select()
                    if ready:
                        # Receive a frame, ETH_FRAME_LEN = 1514
                        frame = server_socket.recv(ETH_FRAME_LEN)
                        # Extract a header, ETH_HLEN = 14
                        header = frame[:ETH_HLEN]
                        # Unpack an Ethernet header in network byte order
                        dst, src, proto = struct.unpack('!6s6sH', header)
                        # Extract a payload
                        payload = frame[ETH_HLEN:]
                        print('src byte = ', bytes_to_eui48(src))
                        print('dst byte = ', bytes_to_eui48(dst))
                        print('payload = ', payload)
                        if src == b'\x00\x00\x00\x00\x00\x01':
                            print(f'dst: {bytes_to_eui48(dst)}, \n'
                                  f'src: {bytes_to_eui48(src)}, \n'
                                  f'type: {hex(proto)}, \n'
                                  f'payload: {payload[:ETH_DATA_LEN]}...')
    
    stopThreads = False
    receiveRawData = threading.Thread(target=receiveSocket)
    sendRawData = threading.Thread(target=sendSocket)
    receiveRawData.start()
    sendRawData.start()
    sendRawData.join()
    stopThreads = True
    receiveRawData.join()
    '''    
    
class receiveSocket(threading.Thread):
    def __init__(self, interface):
        threading.Thread.__init__(self)
        self.interface = interface
        print('receiveSocket __init__')

    def run(self):
        with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as server_socket:
            # Bind the interface
            server_socket.bind((self.interface, 0))
            with selectors.DefaultSelector() as selector:
                # Resister the socket for selection, monitoring it for I/O events
                selector.register(server_socket.fileno(), selectors.EVENT_READ)
                while True:
                    if stopThreads:
                        break
                    # Wait until the socket become readable
                    ready = selector.select()
                    if ready:
                        # Receive a frame, ETH_FRAME_LEN = 1514
                        frame = server_socket.recv(ETH_FRAME_LEN)
                        # Extract a header, ETH_HLEN = 14
                        header = frame[:16]
                        # Unpack an Ethernet header in network byte order
                        dst, src, index, number, fc = struct.unpack('!6s6ss2ss', header)
                        dataLen = int.from_bytes(number, "big")
                        # Extract a payload
                        payload = frame[16:16+dataLen]
                        #number, fc = struct.unpack('!2ss', payload)
                        
                        # ETH_DATA_LEN = 1500	
                        if src == b'\x00\x00\x00\x00\x00\x20':
                            print(f'Destination Address: {bytes_to_eui48(dst)}, \n'
                                  f'Source Address: {bytes_to_eui48(src)}, \n'
                                  f'Package Index: {int.from_bytes(index, "big")}, \n'
                                  f'Number of Data Byte: {int.from_bytes(number, "big")}, \n'
                                  # f'payload: {payload[:ETH_DATA_LEN]}...')
                                  f'Flow Ctrl: {fc}, \n'
                                  f'Data: {payload}')
                print("Done.")    
        
# interface, destinationAdd, flowCtrl, rawData, eth0
testRawID = setRaw('eno2', b'\x00\x00\x00\x00\x00\x00', b'\x10', '1122334420') #Set ID
testRawWrite = setRaw('eno2', b'\x00\x00\x00\x00\x00\x20', b'\x1E', '0400000011121314') #Write Register
testRawRead = setRaw('eno2', b'\x00\x00\x00\x00\x00\x20', b'\x1F', '040000000400') #Read Register
fpgaOTA = setRaw('eno2', b'\x00\x00\x00\x00\x00\x20', b'\x11', '00000000') #Read Register
receiveRaw = receiveSocket('eno2')
stopThreads = False #receiveSocket
receiveRaw.start()

time.sleep(2)
testRawID.start()
time.sleep(2)
testRawWrite.start()
time.sleep(2)
testRawRead.start()
time.sleep(2)
fpgaOTA.start()
stopThreads = True
time.sleep(1)
receiveRaw.join()
