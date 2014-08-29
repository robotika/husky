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
        self.buf = ""
    
    def readMsg( self ):
        try:
            data = self.readFn( 4096 )
        except socket.timeout as e:
            print e # it should contain partial data            
        except socket.error as (errno, errStr):
            assert errno == 10035, (errno, errStr) # i.e. not 'A non-blocking socket operation could not be completed immediately'
            data = ""
        self.logFile.write( data )
        self.logFile.flush()
        self.buf += data
        if len(self.buf) >= 4:
            num = struct.unpack("I", self.buf[:4])[0]
            if len(self.buf) >= 4 + num:
                data = self.buf[4:4+num]
                self.buf = self.buf[4+num:]
                return data
        return None


class Tcpros:
    "TCPROS communication protocol"
    def __init__( self, readFn=None, readMsgFn=None ):
        self.readFn = readFn
        self.readMsgFn = readMsgFn
        self.topicType = None

    def readMsg( self ):
        "skip very first message - topic description"
        if self.topicType == None:
            m = self._readMsg()
            if m != None:
                self.topicType = splitLenStr(m)
                for s in self.topicType:
                    print s
            return None
        return self._readMsg()

    def _readMsg( self ):
        if self.readMsgFn:
            return self.readMsgFn()
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

