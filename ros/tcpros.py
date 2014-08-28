"""
  Parsing TCPROS communication protocol
  usage:
     ./tcpros <log file to replay>
"""

import socket
import struct
import sys
import datetime

def prefix4BytesLen( s ):
    "adding ROS length"
    return struct.pack("I", len(s)) + s

def splitLenStr( data ):
    ret = []
    while len(data) >= 4:
        size = struct.unpack( "I", data[:4] )[0]
        data = data[4:]
        ret.append( data[:size] )
        data = data[size:]
    return ret

class LoggedStream:
    def __init__( self, readFn, prefix ):
        self.readFn = readFn
        dt = datetime.datetime.now()
        filename = prefix + dt.strftime("%y%m%d_%H%M%S.log") 
        self.logFile = open( filename, "wb" )
        print "LogIt:", filename 
    
    def read( self, num ):
        data = self.readFn( num )
        self.logFile.write( data )
        self.logFile.flush()
        return data

class Tcpros:
    "TCPROS communication protocol"
    def __init__( self, readFn ):
        self.readFn = readFn
        self.topicType = splitLenStr(self.readMsg())
        for s in self.topicType:
            print s

    def readMsg( self ):
        data = self.readFn(4)
        if len(data) == 0:
            return None
        size = struct.unpack("I", data)[0]
        return self.readFn( size )

if __name__ == "__main__":
    from msgs import *
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1) 
    t = Tcpros( open(sys.argv[1], "rb").read )
    while 1:
        m = t.readMsg()
        if m == None:
            break
#        print t.parseImu(m)
#        print t.parseEncoders(m)
#        print t.parsePower(m)
        print parseString(m)
        print "--------------"


#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

