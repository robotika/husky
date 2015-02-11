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

def view( filename ):
    if filename.endswith(".gz"):
        data = gzip.open( filename, "rb" ).read()
    else:
        data = open( filename, "rb" ).read()
    assert len(data) % (320*240) == 0
    atomSize = len(data)/(320*240)
    assert atomSize in [2,3], atomSize
    if atomSize == 2:
        # depth
        arr = struct.unpack("<" + "H"*(240*320), data)
        depth = np.array( arr, dtype=np.uint16 )
        depth.shape = (240, 320, 1)
        centerArea = depth[120-40:120+40, 160-40:160+40]
        mask = centerArea > 0
        if centerArea.max() > 0:
            print "Min dist", centerArea[mask].min()/1000.0
        img = np.array( [x/20 for x in arr], dtype=np.uint8 )
        img.shape = (240, 320, 1)
    else:
        # color
        img = np.array( [ord(x) for x in data], dtype=np.uint8 )
        img.shape = (240, 320, 3)
        img = cv2.cvtColor( img, cv2.COLOR_BGR2RGB )
    img = cv2.flip( img, 1 )
    cv2.imshow("image",img)
    cv2.waitKey()
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(2)
    view( sys.argv[1] )

# vim: expandtab sw=4 ts=4 

