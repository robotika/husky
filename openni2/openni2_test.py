import unittest
import numpy as np
import gzip

class OpenNI2Test( unittest.TestCase ): 

    def test16bitArray( self ):
        arr = np.array([1,2,3], dtype=np.uint16)
        f = gzip.open("tmp.bin.gz", "wb")
        f.write( arr )
        f.close()
        f = gzip.open("tmp.bin.gz", "rb")
        print len(f.read())
        f.close()

if __name__ == "__main__":
    unittest.main() 

# vim: expandtab sw=4 ts=4

