#!/usr/bin/python
"""
  ROS wrapper for Husky
  usage:
     ./huskyros.py [<metalog file> [F]|<IP node> <IP master>]
"""

from node import NodeROS, setIPs
import sys
import math

def normalizeAnglePIPI( angle ):
    while angle < -math.pi:
        angle += 2*math.pi
    while angle > math.pi:
        angle -= 2*math.pi
    return angle 


class HuskyROS:
    def __init__( self, filename=None, replay=False, assertWrite=True, ipPair=None ):
        if ipPair is not None:
            setIPs( *ipPair )
        self.node = NodeROS( 
            subscribe=['/imu/data', '/imu/mag', '/imu/rpy', '/imu/temperature',
                '/husky/data/encoders', 
                '/husky/data/power_status',
                '/husky/data/safety_status', 
                '/joy', 
                '/husky/data/system_status'], 
            publish=['/husky/cmd_vel'],
            heartbeat='/husky/data/encoders',                
            filename=filename, replay=replay, assertWrite=assertWrite )
        self.speed = 0.0
        self.angularSpeed = 0.0
        self.enc = None # unknown
        self.time = None
        self.power = None
        self.imu = None
        self.mag = None
        self.azimuth = None
        self.greenPressed = None
        self.redPressed = None
        self.joyAxis = (0,0, 0,0, 0,0)
        self.update()

    def update( self ):
        self.node.cmdList.append( ('/husky/cmd_vel', (self.speed,self.angularSpeed)) )
        status = self.node.update()
        for topic,data in status:
            if topic == '/joy':
                self.joyAxis, buttons = data
                self.greenPressed = (buttons[1]==1)
                self.redPressed = (buttons[2]==1)
            if topic == '/imu/data':
                q0,q1,q2,q3 = data # quaternion
#                print "[%.2f %.2f %.2f]" % (1-2*(q2*q2+q3*q3), 2*(q1*q2-q0*q3), 2*(q0*q2+q1*q3)),
#                print "[%.2f %.2f %.2f]" % (2*(q1*q2+q0*q3), 1-2*(q1*q1+q3*q3), 2*(q2*q3-q0*q1)),
#                print "[%.2f %.2f %.2f]" % (2*(q1*q3-q0*q2), 2*(q0*q1+q2*q3), 1-2*(q1*q1+q2*q2))
#                a2 = math.acos(q0)   # q0 = cos(alpha/2)
#                sinA2 = math.sin(a2)
#                bx = math.acos(q1/sinA2) # q1 = sin(alpha/2)*cos(bx)
#                by = math.acos(q2/sinA2)
#                bz = math.acos(q3/sinA2)
#                self.imu = data[:]
#                print bx, by, bz #math.degrees(2*a2)
                self.imu =  math.atan2(2*(q0*q1+q2*q3), 1-2*(q1*q1+q2*q2)) # along X axis
#                self.imu =  math.degrees( math.asin(2*(q0*q2-q3*q1)) ) # along Y axis ... max 5deg
#                self.imu =  math.degrees( math.atan2(2*(q0*q3+q1*q2), 1-2*(q2*q2+q3*q3)) ) # along Z axis ~80 deg
            if topic == '/imu/mag':
                self.mag = data[:]
                self.azimuth = math.atan2( data[2], data[0] )

            if topic == '/husky/data/encoders':
                self.time = data[0]
                self.enc = data[1][0], data[2][0] # only distance traveled

            if topic == '/husky/data/power_status':
                self.power = data

    def setSpeedPxPa( self, speed, angularSpeed ):
        self.speed = speed
        self.angularSpeed = angularSpeed

    def goStraight( self, dist, maxSpeed=0.1 ):
        "go forward for given distance"
        print "GO!", dist, maxSpeed
        assert self.enc != None
        prevEncL, prevEncR = self.enc
        startTime = self.time
        while ((self.enc[0]-prevEncL) + (self.enc[1]-prevEncR))/2.0 < dist:
            self.setSpeedPxPa( maxSpeed, 0 )
            self.update()
        self.setSpeedPxPa( 0, 0 )
        self.update()
        print "TIME", self.time-startTime

    def turn( self, angle ):
        "go forward for given distance"
        WIDTH = 0.55
        assert self.enc != None
        prevEncL, prevEncR = self.enc
        startTime = self.time
        prevImu = self.imu
#        while abs((self.enc[0]-prevEncL) - (self.enc[1]-prevEncR)) < WIDTH*angle:  # unusable
        while abs( normalizeAnglePIPI(self.imu - prevImu) ) < angle:
            self.setSpeedPxPa( 0.0, 0.3 )
            self.update()
        self.setSpeedPxPa( 0, 0 )
        self.update()
        print "TIME", self.time-startTime, math.degrees( normalizeAnglePIPI(self.imu - prevImu) )


    def turnToAzimuth( self, azimuth ):
        print "AZI", math.degrees( self.azimuth ), math.degrees( azimuth )
        while abs( normalizeAnglePIPI(self.azimuth - azimuth) ) > math.radians(2):
            self.setSpeedPxPa( 0.0, 0.3 )
            self.update()
        self.setSpeedPxPa( 0, 0 )
        self.update()


    def wait( self, seconds ):
        startTime = self.time
        while startTime + seconds > self.time:
            self.setSpeedPxPa( 0.0, 0.0 )
            self.update()


def test( robot ):
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


def test2( robot ):
    VEL_SCALE = 0.5
    ROT_SCALE = 1.0 
    prevPressed = False
    prevEnc = robot.enc[:]
    while True:
        robot.update()
        if not prevPressed and robot.greenPressed:
            print robot.azimuth, prevEnc[0] - robot.enc[0], prevEnc[1] - robot.enc[1]
            prevEnc = robot.enc[:]
        if robot.greenPressed:
            robot.speed = VEL_SCALE*robot.joyAxis[1]
            robot.angularSpeed = ROT_SCALE*robot.joyAxis[0]
        else:
            robot.speed,robot.angularSpeed = 0,0
        prevPressed = robot.greenPressed
        if robot.redPressed:
            print "RED"
            break
    robot.speed = 0.0
    robot.update()



def test3( robot ):
    print math.degrees(robot.imu), robot.mag, math.degrees(robot.azimuth)
    robot.goStraight( 1.0 )
    print math.degrees(robot.imu), robot.mag, math.degrees(robot.azimuth)
    robot.wait( 3 )
    print math.degrees(robot.imu), robot.mag, math.degrees(robot.azimuth)
    robot.turn( math.radians(90) )
    print math.degrees(robot.imu), robot.mag
    robot.wait( 3 )
    print math.degrees(robot.imu), robot.mag


def test4( robot ):
    robot.wait( 3 )
    for i in xrange(20):
        robot.wait( 2 )
        print math.degrees(robot.azimuth)
        robot.turn( math.radians(20) )
    robot.wait( 3 )

def test5( robot ):
    for i in xrange(5):
        robot.turnToAzimuth( math.radians(0.0) )
        robot.goStraight( 1.0 )
        robot.turnToAzimuth( math.radians(180.0) )
        robot.goStraight( 1.0 )


def test6( robot ):
    for azi,dist in [ (-1.13311392218, 11.091),
            (0.175614628559, 3.584),
            (1.62315635666, 11.842),
            (-2.77704236902, 4.407),
            (-1.14243399246, 1.0)]: # unknown
        robot.turnToAzimuth( azi )
        robot.goStraight( dist, maxSpeed=0.3 )

if __name__ == "__main__":
    if len(sys.argv) < 2 or (len(sys.argv)==2 and "meta" not in sys.argv[1]):
        print __doc__
        sys.exit(1)

    filename = None
    assertWrite = True
    if "meta" in sys.argv[1]:
        filename = sys.argv[1]
        if len(sys.argv) > 2 and sys.argv[2] == 'F':
            assertWrite = False
    else:
        setIPs( sys.argv[1], 'http://'+sys.argv[2]+':11311' )
    robot = HuskyROS( filename=filename, assertWrite=assertWrite )
    test6( robot )

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4 

