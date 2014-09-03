#!/usr/bin/python
"""
  ROS wrapper for Husky
  usage:
     ./husky.py <task> [<metalog file>]
"""

from node import NodeROS, setIPs
import sys

class HuskyROS:
    def __init__( self, metalog=None ):
        self.node = NodeROS( 
            subscribe=['/imu/data', 
                '/husky/data/encoders', 
                '/husky/data/power_status',
                '/husky/data/safety_status', 
                '/joy', 
                '/husky/data/system_status'], 
            publish=['/husky/cmd_vel'],
            heartbeat='/husky/data/encoders',                
            metalog=metalog )
        self.speed = 0.0
        self.angularSpeed = 0.0
        self.greenPressed = None
        self.redPressed = None

    def update( self ):
        self.node.cmdList.append( ('/husky/cmd_vel', (self.speed,self.angularSpeed)) )
        status = self.node.update()
        for topic,data in status:
            if topic == '/joy':
                print data
                axes, buttons = data
                self.greenPressed = (buttons[1]==1)
                self.redPressed = (buttons[2]==1)


def test( metalog ):
    robot = HuskyROS( metalog=metalog )
    robot.speed = 0.0
    while True:
        robot.update()
        if robot.greenPressed:
            print "GREEN"
            robot.speed = 0.1
        else:
            print "PAUSE"
            robot.speed = 0.0
        if robot.redPressed:
            print "RED"
            robot.speed = 0.0
            break

    robot.speed = 0.0
    robot.update()


if __name__ == "__main__":
    if len(sys.argv) < 2 or (len(sys.argv)==2 and "meta" not in sys.argv[1]):
        print __doc__
        sys.exit(1)

    metalog = None
    if "meta" in sys.argv[1]:
        metalog = sys.argv[1]
    else:
        setIPs( sys.argv[1], 'http://'+sys.argv[2]+':11311' )
    test( metalog )

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4 

