#!/usr/bin/python
"""
  Check current Husky battery status (via ROS)
  usage:
      ./battery.py [<node IP> <master IP> | -m <metalog> [F]]
"""
import sys
import os
from huskyros import HuskyROS

# apyros should be common lib - now in katarina code
from apyros.sourcelogger import SourceLogger
from apyros.metalog import MetaLog, disableAsserts

def battery( metalog, assertWrite, ipPair ):
    if metalog is None:
        metalog = MetaLog()
        robot = HuskyROS( filename=metalog.getLog("node"), replay=metalog.replay, ipPair=ipPair )
    else:
        robot = HuskyROS( filename=metalog.getLog("node"), replay=True, assertWrite=assertWrite, ipPair=ipPair ) # TODO move assert to metalog
        scannerFn = SourceLogger( sourceGet=None, filename=metalog.getLog("scanner") ).get
    robot.setSpeedPxPa( 0, 0 )
    for i in xrange(10):
        robot.update()
    print "Battery: %.3f" % robot.power


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
    else:
        ipPair = ( sys.argv[1], 'http://'+sys.argv[2]+':11311' )
    battery( metalog, assertWrite, ipPair )

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

