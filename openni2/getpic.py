#!/usr/bin/python
"""
  Wrapper for PrimeSense 3D sensor
  usage:
       ./getpic.py <num images>
"""

from primesense import openni2
import gzip
import sys
import datetime
import struct

class Sensor3D:
    def __init__( self ):
        openni2.initialize()
        self.dev = openni2.Device.open_any()
        self.depth_stream = self.dev.create_depth_stream()
        self.col = self.dev.create_color_stream()
        self.index = 0
        self.depth_stream.start()
        self.col.start()

    def save( self, prefix, data ):
        f = gzip.open( prefix + datetime.datetime.now().strftime("_%y%m%d_%H%M%S") + "_%03d" % self.index + \
                ".bin.gz", "wb" )
        f.write( "".join([struct.pack("H", x) for x in data]) )
        f.close()
        self.index += 1

    def readDepth( self ):
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_uint16()
        return frame_data

    def readColor( self ):
        frame = self.col.read_frame()
        print frame.width, frame.height
        frame_data = frame.get_buffer_as_uint16()
        return frame_data

def test( num ):
    s = Sensor3D()
    for i in xrange( num ):
        s.save( "logs/depth", s.readDepth() )
        s.save( "logs/pic", s.readColor() )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(2)
    test( int(sys.argv[1]) )

# vim: expandtab sw=4 ts=4 

