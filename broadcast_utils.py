import log_utils # utils.log_utils
import socket
import selectors
import struct
import binascii
import time

from ethernet import *

log = log_utils.logging_init(__file__) # utils.log_utils.logging_init(__file__)

# Broadcast: Destination address = 0 
# flowCtrl: 0x10=Set ID, 0x12=Image Flush, 0x1E=Write Register
def broadcast(interface, sourceAdd, flowCtrl, rawData):
    preamble = b'\x55\x55\x55\x55\x55\x55\x55'  #55555555555555
    sof = b'\xD5'
    # sourceAdd = b'\x00\x00\x00\x00\x00\x01' # 主控
    destinationAdd = b'\x00\x00\x00\x00\x00\x01' # broadcast mode
    packageIndex = b'\x01' 
    rawData = binascii.unhexlify(rawData)
    dataLen = len(rawData) # number of data byte
    if dataLen > 1480:
        print('data length is over MTU!!')
        return
        
    # count CRC
    CRC = 0
    for i in range(len(preamble)):
        CRC += preamble[i]
    
    for i in range(dataLen):
        CRC += rawData[i]
            
    for i in range(len(sourceAdd)):
        CRC += sourceAdd[i]
        
    # for i in range(len(destinationAdd)):
        # CRC += destinationAdd[i]
        
    CRC += sof[0]
    CRC += flowCtrl[0]
    CRC += packageIndex[0]
    CRC += dataLen
    
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW) as client_socket:
        # Bind an interface
        client_socket.bind((interface, 0))
        # Send a frame
        client_socket.sendall(
            # Pack in network byte order (frame)
            struct.pack('!6s6ssHs' + str(dataLen) + 's', #'!6s6ssHs' + str(dataLen) + 's4s',
                        #eui48_to_bytes(self.destinationAdd),
                        destinationAdd,
                        sourceAdd,
                        packageIndex,
                        dataLen, # number of data byte
                        flowCtrl,
                        rawData))
                        #CRC.to_bytes(4, 'big')))  
        print('Sent!')  
        
# interface, sourceAdd, flowCtrl, rawData
#broadcast('eno2', b'\x00\x00\x00\x00\x00\x01', b'\x1E', '02ABCDEFFE')
while True:
    broadcast('eno2', b'\x00\x00\x00\x00\x00\x20', b'\x9E', '0000000000ffffffffffffff000000000000000000000000ffff0000000000000000ffffbfbf000000000000')
    time.sleep(1)