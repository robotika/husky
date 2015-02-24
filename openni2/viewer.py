#!/usr/bin/python
"""
  View depth/color data from PrimeSense 3D sensor
  usage:
       ./viewer.py <filename>
"""

import gzip
import sys
import cv2
import numpy as np
import struct
import os

def view( filename, pause=0 ):
    if filename.endswith(".gz"):
        data = gzip.open( filename, "rb" ).read()
    else:
        data = open( filename, "rb" ).read()
    assert len(data) % (320*240) == 0
    atomSize = len(data)/(320*240)
    assert atomSize in [2,3], atomSize
    pt = None
    if atomSize == 2:
        # depth
        arr = struct.unpack("<" + "H"*(240*320), data)
        depth = np.array( arr, dtype=np.uint16 )
        depth.shape = (240, 320, 1)
        centerArea = depth[120-40:120+40, 160-40:160+40]
        mask = centerArea == 0
        centerArea[mask] = 10000
        print "Min dist", centerArea.min()/1000.0, 
        i = centerArea.argmin()
        pt = (120-40 + i / 80, 160-40 + i % 80 )
        print pt, centerArea[i/80,i%80]
        img = np.array( [x/20 for x in arr], dtype=np.uint8 )
        img.shape = (240, 320, 1)
    else:
        # color
        img = np.array( [ord(x) for x in data], dtype=np.uint8 )
        img.shape = (240, 320, 3)
        img = cv2.cvtColor( img, cv2.COLOR_BGR2RGB )
    if pt:
        cv2.circle( img, center=(pt[1],pt[0]), radius=10, color=(255,0,0) )
    img = cv2.flip( img, 1 )
    cv2.imshow("image",img)
    ch = cv2.waitKey( pause )
    if ch == ord('s'):
        cv2.imwrite( "tmp.jpg", img )
        print "Image saved"
    if ch == 27:
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(2)
    if ".bin" in sys.argv[1]:
        view( sys.argv[1] )
    else:
        for filename in os.listdir( sys.argv[1] ):
            if ".bin" in filename:
                print filename
                view( os.path.join( sys.argv[1], filename ), pause=100 )

# vim: expandtab sw=4 ts=4 

