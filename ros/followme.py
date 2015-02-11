#!/usr/bin/python
"""
  Follow Me with Husky (ROS) and PrimeSense sensor (direct OpenNI2)
  usage:
      ./followme.py [<node IP> <master IP> | <metalog>]
"""
import sys
import os
from threading import Thread,Event,Lock 
from huskyros import HuskyROS

sys.path.append( ".."+os.sep+"openni2") 
from getpic import Sensor3D
import numpy as np
import datetime

class ScannerThread( Thread ):
    def __init__( self ):
        Thread.__init__(self)
        self.setDaemon(True) 
        self.shouldIRun = Event()
        self.shouldIRun.set()
        self.sensor = Sensor3D() 
        self.minDist = None # i.e. unknown

    def run( self ):
        while self.shouldIRun.isSet(): 
            arr = self.sensor.readDepth()
            depth = np.array( arr, dtype=np.uint16 )
            depth.shape = (240, 320, 1)
            centerArea = depth[120-40:120+40, 160-40:160+40]
            mask = centerArea > 0
            if centerArea.max() == 0:
                self.minDist = 10.0
            else:
                self.minDist = centerArea[mask].min()/1000.0
            print "Min dist", self.minDist
            self.sensor.save( "logs/depth", arr )
            self.sensor.save( "logs/pic", self.sensor.readColor() ) 

    def requestStop(self):
        self.shouldIRun.clear() 


def followme( metalog, assertWrite, ipPair ):
    print "Follow Me"
    robot = HuskyROS( metalog=metalog, assertWrite=assertWrite, ipPair=ipPair )
    print "started"
    if metalog is None:
        scanner = ScannerThread()
        scanner.start()
    maxSpeed = 0.1
    safeDist = 1.0
    index = 0
    prev = None
    log = open( datetime.datetime.now().strftime("logs/scanner_%y%m%d_%H%M%S.log"), "w" )
    while True:
        if scanner.minDist != prev:
            prev = scanner.minDist
            log.write("%d\n" % index )
            log.write("%.3f\n" % prev )
            log.flush()
            index = 0
        index += 1

        if prev is None or prev < safeDist:
            robot.setSpeedPxPa( 0, 0 )
        else:
            robot.setSpeedPxPa( maxSpeed, 0 )
        robot.update()
    robot.setSpeedPxPa( 0, 0 )
    robot.update()
    log.write("%d\n" % index )
    log.close()

    if metalog is None:
        scanner.requestStop()
        scanner.join()
 

if __name__ == "__main__":
    if len(sys.argv) < 2 or (len(sys.argv)==2 and "meta" not in sys.argv[1]):
        print __doc__
        sys.exit(1)

    metalog = None
    assertWrite = True
    ipPair = None
    if "meta" in sys.argv[1]:
        metalog = sys.argv[1]
        if len(sys.argv) > 2 and sys.argv[2] == 'F':
            assertWrite = False
    else:
        ipPair = ( sys.argv[1], 'http://'+sys.argv[2]+':11311' )
    followme( metalog, assertWrite, ipPair )

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

