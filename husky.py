#!/usr/bin/python
"""
  Light weight wrapper to Husky
"""

import sys
import serial
import struct
from logit import *
from crc16 import ccitt_checksum as checksum

REQ_PLATFORM_INFO = 0x4001


class Husky:
  def __init__( self, com ):
    self.com = com
    self.timestamp = 0

  def sendPacket( self, messageType, data = "" ):
    packet = struct.pack( 'BBBBIBHB',
    0xAA,           # SAH
    len(data),      # data length + compliment
    255-len(data),
    1,              # version
    self.timestamp, # unique number for ACK
    0,              # flags
    messageType,    # 16bit
    0x55 )          # STX - data start
    packet += data
    packet += struct.pack("H", checksum( [ord(x) for x in packet] ))
    print repr(packet)
    self.timestamp += 1
    self.com.write( packet )

def main():
  robot = Husky( LogIt( serial.Serial( '/dev/ttyUSB1', 115200 ) ) )
  robot.sendPacket( REQ_PLATFORM_INFO )
  while 1:
    print hex(ord(robot.com.read(1)))

if __name__ == "__main__":
  main()
