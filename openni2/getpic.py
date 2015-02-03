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

class Sensor3D:
    def __init__( self ):
        openni2.initialize()
        self.dev = openni2.Device.open_any()
        self.depth_stream = self.dev.create_depth_stream()
        self.col = self.dev.create_color_stream()
        self.index = 0

    def save( self, prefix, data ):
        f = gzip.open( prefix + datetime.datetime.now().strftime("_%y%m%d_%H%M%S") + "_%03d" % self.index + \
                ".bin.gz", "wb" )
        f.write( data )
        f.close()
        self.index += 1

    def readDepth( self ):
        self.depth_stream.start()
        frame = self.depth_stream.read_frame()
        frame_data = frame.get_buffer_as_uint16()
        self.depth_stream.stop()
        return frame_data

    def readColor( self ):
        self.col.start()
        frame = self.col.read_frame()
        print frame.width, frame.height
        self.col.stop()
        frame_data = frame.get_buffer_as_uint16()
        return frame_data

def test( num ):
    s = Sensor3D()
    for i in xrange( num ):
        s.save( "depth", s.readDepth() )
        s.save( "pic", s.readColor() )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(2)
    test( int(sys.argv[1]) )

# vim: expandtab sw=4 ts=4 

