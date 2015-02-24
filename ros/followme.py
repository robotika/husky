#!/usr/bin/python
"""
  Follow Me with Husky (ROS) and PrimeSense sensor (direct OpenNI2)
  usage:
      ./followme.py [<node IP> <master IP> | -m <metalog> [F]]
  OR
      ./followme.py -d <depth image>
"""
import sys
import os
from threading import Thread,Event,Lock 
from huskyros import HuskyROS

sys.path.append( ".."+os.sep+"openni2") 
from getpic import Sensor3D
import numpy as np
import datetime

import struct
import gzip

# apyros should be common lib - now in katarina code
from apyros.sourcelogger import SourceLogger
from apyros.metalog import MetaLog, disableAsserts

def processDepth( depth ):
    centerArea = depth[120-40:120+40, 160-40:160+40]
    mask = centerArea == 0
    centerArea[mask] = 10000
    minDist = centerArea.min()
    i = centerArea.argmin()
    return minDist, 160-40+i%80, 120-40+i/80


class ScannerThread( Thread ):
    def __init__( self ):
        Thread.__init__(self)
        self.setDaemon(True) 
        self.shouldIRun = Event()
        self.shouldIRun.set()
        self.lock = Lock()
        self.sensor = Sensor3D() 
        self.minDist = None # i.e. unknown

    def run( self ):
        while self.shouldIRun.isSet(): 
            arr = self.sensor.readDepth()
            self.sensor.save( "logs/depth", arr )
            depth = np.array( arr, dtype=np.uint16 )
            depth.shape = (240, 320, 1)
            tmp = processDepth( depth )
            self.lock.acquire()
            self.minDist = tmp
            self.lock.release()        
            print "Min dist", self.minDist
            self.sensor.save( "logs/pic", self.sensor.readColor() ) 

    def requestStop(self):
        self.shouldIRun.clear() 

    def get(self):
        self.lock.acquire()
        ret = self.minDist
        self.lock.release()        
        return ret


def followme( metalog, assertWrite, ipPair ):
    print "Follow Me"
    if metalog is None:
        metalog = MetaLog()
        robot = HuskyROS( filename=metalog.getLog("node"), replay=metalog.replay, ipPair=ipPair )
        print "started"
        scanner = ScannerThread()
        scanner.start()
        scannerFn = SourceLogger( sourceGet=scanner.get, filename=metalog.getLog("scanner") ).get
    else:
        robot = HuskyROS( filename=metalog.getLog("node"), replay=True, assertWrite=assertWrite, ipPair=ipPair ) # TODO move assert to metalog
        scannerFn = SourceLogger( sourceGet=None, filename=metalog.getLog("scanner") ).get
    maxSpeed = 0.5
    safeDist = 0.5
    index = 0
    prev = None
    while True:
        minDist = scannerFn()
        if minDist is not None:
            prev = minDist[0]/1000.0
            print prev

        if prev is None or prev < safeDist:
            robot.setSpeedPxPa( 0, 0 )
        elif prev < safeDist*2:
            robot.setSpeedPxPa( maxSpeed/2, 0 )
        elif prev < safeDist*3:
            robot.setSpeedPxPa( maxSpeed, 0 )
        else:
            robot.setSpeedPxPa( 2*maxSpeed, 0 )
        robot.update()
    robot.setSpeedPxPa( 0, 0 )
    robot.update()
    log.write("%d\n" % index )
    log.close()

    if not metalog.replay:
        scanner.requestStop()
        scanner.join()
 

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print __doc__
        sys.exit(1)

    metalog = None
    assertWrite = True
    ipPair = None
    if sys.argv[1] == '-m':
        metalog = MetaLog( filename = sys.argv[2] )
        if len(sys.argv) > 3 and sys.argv[3] == 'F':
            assertWrite = False
            disableAsserts()
    elif sys.argv[1] == '-d':
        # TODO move into sensor load() function
        data = gzip.open( sys.argv[2], "rb").read()
        arr = struct.unpack("<" + "H"*(240*320), data)
        depth = np.array( arr, dtype=np.uint16 )
        depth.shape = (240, 320, 1)
        print processDepth( depth )
        sys.exit(0)
    else:
        ipPair = ( sys.argv[1], 'http://'+sys.argv[2]+':11311' )
    followme( metalog, assertWrite, ipPair )

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

