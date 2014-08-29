"""
  'Database' of messages
"""

import struct

def parseNone( data ):
    "dummy parser"
    return len(data)

def parseString( data ):
    n = struct.unpack("I", data[:4])[0]
    return data[4:4+n]


def parseImu( data ):
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


def parseEncoders( data ):
    seq, stamp, stampNsec, frameIdLen = struct.unpack("IIII", data[:16])
    print seq, stamp, stampNsec, frameIdLen
    assert frameIdLen == 0, frameIdLen
    data = data[16+frameIdLen:]
    arrLen, travelL,speedL, travelR,speedR = struct.unpack("=Idddd", data)
    assert arrLen==2, arrLen
    return (travelL,speedL), (travelR,speedR)


def parsePower( data ):
    seq, stamp, stampNsec, frameIdLen = struct.unpack("IIII", data[:16])
    print seq, stamp, stampNsec, frameIdLen
    assert frameIdLen == 0, frameIdLen
    data = data[16+frameIdLen:]
    arrLen, charge, capacity, present, inUse, description = struct.unpack("=Ifh??B", data)
    assert arrLen==1, arrLen
    return charge

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

