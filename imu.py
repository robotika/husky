#!/usr/bin/python
"""
  Light weight wrapper for Chrobotics UM6 IMU
  usage:
     ./imu.py <task> [<replay log file> [F|FF]]
"""
# https://www.chrobotics.com/docs/UM6_datasheet.pdf
# http://wiki.ros.org/um6

import sys
import serial
import struct
from logit import *

class IMU:
    def __init__( self, com ):
        self.com = com
        self.config()

    def sendPacket( self, messageType, data = "" ):
        pass

    def readPacket( self ):
        data = self.com.read(7) # minimal size
        while not data.startswith( "snp" ):
            data = data[1:] + self.com.read(1)
        return data
        

    def config( self ):
        pass

    def update( self ):
        packet = self.readPacket()
        print "".join(["%02X" % ord(x) for x in packet])


def testUsage( com ):
    "log available data"
    imu = IMU( com )
    for i in xrange(100):
        imu.update()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1)
    filename = None
    com = None
    if len(sys.argv) > 2:
        replayAssert = True
        filename = sys.argv[2]
        if len(sys.argv) > 3:
            assert sys.argv[3] in ['F','FF']
            if sys.argv[2] == 'F':
                replayAssert = False
            else:
                com = ReplyLogInputsOnly( filename )
    if filename:
        if com == None:
            com = ReplayLog( filename, assertWrite=replayAssert )
    else:
        com = LogIt( serial.Serial( '/dev/ttyUSB0', 115200 ), prefix='logs/imu' )
    testUsage( com )

# vim: expandtab sw=4 ts=4 

