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
    def __init__( self, readFn=None, writeFn=None, prefix="" ):
        self.readFn = readFn
        self.writeFn = writeFn
        dt = datetime.datetime.now()
        self.filename = prefix + dt.strftime("%y%m%d_%H%M%S.log") 
        self.logFile = open( "logs/" + self.filename, "wb" )
        print "LogIt:", self.filename 
        self.buf = ""
    
    def readMsg( self ):
        try:
            data = self.readFn( 4096 )
        except socket.timeout as e:
            assert False, e # it should contain partial data            
        except socket.error as (errno, errStr):
            assert errno in [10035,11], (errno, errStr) 
               # Windows 'A non-blocking socket operation could not be completed immediately'
               # Linux (11, 'Resource temporarily unavailable')
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

    def writeMsg( self, msg ):
        data = prefix4BytesLen( msg )
        self.logFile.write( data )
        self.logFile.flush()
        self.writeFn( data )



class ReplayLoggedStream:
    def __init__( self, filename, assertWrite ):
        self.filename = filename
        self.logFile = open( self.filename, "rb" )
        print "ReplayLog:", self.filename 
        self.assertWrite = assertWrite
    
    def readMsg( self ):
        data = self.logFile.read( 4 )
        if len(data) >= 4:
            num = struct.unpack("I", data[:4])[0]
            return self.logFile.read( num )
        return None

    def writeMsg( self, msg ):
        data = prefix4BytesLen( msg )
        ref = self.logFile.read( len(data) )
        if self.assertWrite:
            assert data == ref, (ref,data)



class Tcpros:
    "TCPROS communication protocol"
    def __init__( self, readFn=None, readMsgFn=None, verbose=False ):
        self.readFn = readFn
        self.readMsgFn = readMsgFn
        self.topicType = None
        self.verbose = verbose

    def readMsg( self ):
        "skip very first message - topic description"
        if self.topicType == None:
            m = self._readMsg()
            if m != None:
                self.topicType = splitLenStr(m)
                if self.verbose:
                    for s in self.topicType:
                        print s
                return self._readMsg()
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
#        print parseString(m)
#        print parseJoy(m)
        print parseSafety(m)
        print "--------------"


#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

