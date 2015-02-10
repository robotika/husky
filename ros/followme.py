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


class ScannerThread( Thread ):
    def __init__( self ):
        Thread.__init__(self)
        self.setDaemon(True) 
        self.shouldIRun = Event()
        self.shouldIRun.set()
        self.sensor = Sensor3D() 

    def run( self ):
        while self.shouldIRun.isSet(): 
            self.sensor.save( "depth", self.sensor.readDepth() )
            self.sensor.save( "pic", self.sensor.readColor() ) 

    def requestStop(self):
        self.shouldIRun.clear() 


def followme( metalog, assertWrite, ipPair ):
    print "Follow Me"
    robot = HuskyROS( metalog=metalog, assertWrite=assertWrite, ipPair=ipPair )
    print "started"
    if metalog is None:
        scanner = ScannerThread()
        scanner.start()
    robot.goStraight( 1.0 )
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

