#!/usr/bin/python
"""
  Light weight wrapper to Husky
  usage:
     ./husky.py <task> [<replay log file> [F|FF]]
"""

import sys
import serial
import struct
from logit import *
from crc16 import ccitt_checksum as checksum

PROTOCOL_VERSION = 1

REQ_PLATFORM_INFO = 0x4001
REQ_FIRMWARE_INFO = 0x4003
REQ_MAX_SPEED = 0x4210
REQ_MAX_ACCEL = 0x4211
REQ_GPIO = 0x4301
REQ_ENCODERS = 0x4800
REQ_SYSTEM_STATUS = 0x4004
REQ_SAFETY_SYSTEM_STATUS = 0x4010

SET_DIFFERENTIAL_OUTPUT = 0x0202

HUSKY_WIDTH = 0.8 # guessed for angular speed

class Husky:
  def __init__( self, com ):
    self.com = com
    self.timestamp = 0
    self.cmdSpeed = (0, 0)
    self.time = None
    self.enc = None
    self.emergencyStopPressed = None
    self.config()

  def sendPacket( self, messageType, data = "" ):
    packet = struct.pack( '=BBBBIBHB',
    0xAA,           # SAH
    len(data)+11,   # data length + compliment
    255-len(data)-11,
    PROTOCOL_VERSION,  # version (in doc is used version 1, but sample code sends 0)
    self.timestamp, # unique number for ACK
    0,              # flags
    messageType,    # 16bit
    0x55 )          # STX - data start
    packet += data
    packet += struct.pack("H", checksum( [ord(x) for x in packet] ))
#    print repr(packet)
    self.timestamp += 1
    self.com.write( packet )

  def _readPacket( self ):
    b = self.com.read(1)
    while b != chr(0xAA):
      print "skipping", hex(ord(b))
      b = self.com.read(1)
    length = ord(self.com.read(1))
    notLength = ord(self.com.read(1))
    assert length+notLength == 0xFF, (length, notLength)
    ret = ""
    for i in xrange(length):
      b = self.com.read(1)
      ret += b
    assert checksum( [0xAA, length, notLength] + [ord(x) for x in ret[:-2]] ) == ord(ret[-2]) + 256*ord(ret[-1])
    version, timestamp, flags, msgType, stx = struct.unpack("=BIBHB", ret[:9])
    assert version == 0x00, version # receiving ver0, but sending ver1
    assert flags == 0, flags
    assert stx == 0x55, stx
    return timestamp, msgType, ret[9:-2]

  def readPacket( self ):
    "wrap communication asserts"
    while True:
      try:
        return self._readPacket()
      except AssertionError, e:
        print e

  def config( self ):
    self.sendPacket( REQ_ENCODERS, data=struct.pack("h", 10 ) ) # at 10Hz    
    self.sendPacket( REQ_FIRMWARE_INFO, data=struct.pack("h", 0 ) ) # once
    self.sendPacket( REQ_MAX_SPEED, data=struct.pack("h", 0 ) ) # once
    self.sendPacket( REQ_MAX_ACCEL, data=struct.pack("h", 0 ) ) # once
    self.sendPacket( REQ_GPIO, data=struct.pack("h", 0 ) ) # once
    self.sendPacket( REQ_SAFETY_SYSTEM_STATUS, data=struct.pack("h", 10 ) ) # 10Hz
    self.sendPacket( REQ_SYSTEM_STATUS, data=struct.pack("h", 1 ) ) # 1Hz


  def update( self ):
    self.sendPacket( SET_DIFFERENTIAL_OUTPUT, data=struct.pack("hh", self.cmdSpeed[0], self.cmdSpeed[1]) )
    for i in xrange(200):
      timestamp, msgType, data = self.readPacket()
#      print hex(msgType)
      if msgType & 0xF000 == 0x4000: # confirmations
        print hex(msgType), [hex(ord(x)) for x in data]
      if msgType in [0x8210, 0x8211, 0x8003 ]:
        print hex(msgType), [hex(ord(x)) for x in data]
      if msgType == 0x8004:
        systemStatusData = struct.unpack( "=IBhhhBhhhBhhhh", data ) # expected 3 voltage/current readings, 4x temperature
#        print systemStatusData
        self.time = systemStatusData[0]/1000.0 # uptime in milisec
      if msgType == 0x8010:
        safetySystemStatusData = struct.unpack( "=H", data )
        self.emergencyStopPressed = ( safetySystemStatusData[0] != 0 )

      if msgType == 0x8800: # Encoder data
        self.enc = struct.unpack( "=Biihh", data ) # expected 2 encoders - position and speed
#        print "ENC", self.enc
        break

  def setSpeedPxPa( self, speed, angularSpeed ):
    diff = angularSpeed * HUSKY_WIDTH/2.0
    self.cmdSpeed = (int((speed-diff)*10000), int((speed+diff)*10000))

  def goStraight( self, dist, maxSpeed=0.3, stop=True ):
    if self.enc is None:    
      for i in xrange(100):
        self.update()
        if self.enc:
          break
    assert self.enc
    assert self.enc[0] == 2, self.enc
    startEnc = (self.enc[1]+self.enc[2])/2
    self.setSpeedPxPa( maxSpeed, 0 )
    while (self.enc[1]+self.enc[2])/2 - startEnc < dist*1000:
      print self.emergencyStopPressed, self.enc
      self.update()
    if stop:
      self.cmdSpeed = (0, 0)
      self.update()

def main0( com ):
  robot = Husky( com )
#  robot.sendPacket( REQ_PLATFORM_INFO )
#  robot.sendPacket( REQ_FIRMWARE_INFO, data=struct.pack("H",0) )
  robot.sendPacket( SET_DIFFERENTIAL_OUTPUT, data=struct.pack("hh", 3000, 3000) )
  for i in xrange(200):
    timestamp, msgType, data = robot.readPacket()
    if msgType == 0x8004:
      # System status data
      uptime, numMeas = struct.unpack( "=IB", data[:5] )
      data = data[5:]
      assert numMeas == 3, numMeas
      volt1, volt2, volt3, numMeas = struct.unpack( "hhhB", data[:6+1] )
      data = data[6+1:]
      print volt1/100., volt2/100., volt3/100., "|",
      assert numMeas == 3, numMeas
      cur1, cur2, cur3, numMeas = struct.unpack( "hhhB", data[:6+1] )
      data = data[6+1:]
      print cur1/100., cur2/100., cur3/100., "|",
      assert numMeas == 4, numMeas
      t1, t2, t3, t4 = struct.unpack( "hhhh", data )
      print t1/100., t2/100., t3/100., t4/100.
    if msgType == 0x8005:
      # Power system status data
      batNum, batState, batCap, batDesc = struct.unpack("=BHHB", data )
      assert batNum == 1, batNum
      assert batDesc == 0xC2, hex(batDesc) # present, in use, Lead-acid battery
      print batState, batCap
    if msgType == 0x8800:
      # Encoder data
      enc = struct.unpack( "=Biihh", data ) # expected 2 encoders - position and speed
      print "ENC", enc
    


def testMotion( com ):
  "slow motion for 25cm (after reseting encoders)"
  robot = Husky( com )
  robot.cmdSpeed = (1000, 1000)
  for i in xrange(100):
    robot.update()
    if robot.enc:
      break
  assert robot.enc
  startEnc = robot.enc[1]
  for i in xrange(1000):
    robot.update()
    if robot.enc and robot.enc[1]-startEnc > 250:
      break
  robot.cmdSpeed = (0, 0)
  robot.update()


def testConfig( com ):
  "sensor configuration should be in Husky constructor - make sure you receive the data"
  robot = Husky( com )
  for i in xrange(10):
    robot.update()


def testRR2015( com ):
  "Robotem Rovne 2015"
  robot = Husky( com )
  robot.cmdSpeed = (10000, 10000)
  while True:
    robot.update()
  robot.cmdSpeed = (0, 0)
  robot.update()


def testFieldDemo( com ):
  robot = Husky( com )
  robot.goStraight( 0.25, maxSpeed = 0.1 )


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print __doc__
    sys.exit(1)
  filename = None
  com = None
  if len(sys.argv) > 2:
    replayAssert = True
    filename = sys.argv[2]
    if len(sys.argv) > 3:
      assert sys.argv[3] in ['F','FF']
      if sys.argv[2] == 'F':
        replayAssert = False
      else:
        com = ReplyLogInputsOnly( filename )
  if filename:
    if com == None:
      com = ReplayLog( filename, assertWrite=replayAssert )
  else:
    com = LogIt( serial.Serial( '/dev/ttyUSB1', 115200 ) )
  testFieldDemo( com )

