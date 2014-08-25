"""
  Parsing TCPROS communication protocol
  usage:
     ./tcpros <log file to replay>
"""

import socket
import struct
import sys

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


class Tcpros:
    "TCPROS communication protocol"
    def __init__( self, filename ):
        self.f = open(filename, "rb")
        self.topicType = splitLenStr(self.readMsg())

    def readMsg( self ):
        data = self.f.read(4)
        if len(data) == 0:
            return None
        size = struct.unpack("I", data)[0]
        return self.f.read( size )

    def parseImu( self, data ):
        seq, stamp, stampNsec, frameIdLen = struct.unpack("IIII", data[:16])
        print seq, stamp, stampNsec, frameIdLen
        print data[16:16+frameIdLen]
        data = data[16+frameIdLen:]
        orientation = struct.unpack("dddd", data[:4*8])
        data = data[4*8+9*8:] # skip covariance matrix
        angularVelocity = struct.unpack("ddd", data[:3*8])
        data = data[3*8+9*8:] # skip velocity covariance
        linearAcceleration = struct.unpack("ddd", data[:3*8])
        data = data[3*8+9*8:] # skip velocity covariance
        assert len(data) == 0, len(data)
        return orientation


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1) 
    t = Tcpros( sys.argv[1] )
    while 1:
        m = t.readMsg()
        if m == None:
            break
        print t.parseImu(m)
        print "--------------"


#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

