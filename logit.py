"""
  Simple read/write wrapper
    robotika.cz
"""

import sys
import serial 
import datetime
import ctypes
import math

class LogEnd(Exception):
  "End of log notification"
  pass 


class LogIt():
  "Log communication via serial com"
  def __init__( self, com ):
    self._com = com
    self._logFile = None
    self.relog( 'logs/hy' )

  def relog( self, prefix ):
    dt = datetime.datetime.now()
    filename = prefix + dt.strftime("%y%m%d_%H%M%S.log") 
    self._logFile = open( filename, "wb" )
    print "LogIt:", filename
    return filename

  def read( self, numChars ):
    s = self._com.read( numChars )
    for ch in s:
      self._logFile.write( chr(0x01) )
      self._logFile.write( ch )
    self._logFile.flush()
    return s

  def write( self, chars ):
    for ch in chars:
      self._logFile.write( chr(0x00) )
      self._logFile.write( ch )
    self._logFile.flush()
    self._com.write( chars ) 

#-------------------------------------------------------------------

class ReplayLog():
  "Read & verify log"
  def __init__( self, filename, assertWrite=True ):
    print "ReplayLog", filename
    self._logFile = open( filename, "rb" )
    self.assertWrite = assertWrite

  def read( self, numChars ):
    s = []
    for i in range(numChars):
      marker = self._logFile.read(1)
      if not marker:
        raise LogEnd()
      assert( marker == chr(0x01) )
      s.append(self._logFile.read(1))
      if not s[-1]:
        raise LogEnd()
    return ''.join(s)

  def write( self, chars ):
    for ch in chars:
      marker = self._logFile.read(1)
      if not marker:
        raise LogEnd()
      assert( marker == chr(0x00) )
      verifyCh = self._logFile.read(1)
      if not verifyCh:
        raise LogEnd()
      if self.assertWrite:
        assert( verifyCh == ch ) 

#-------------------------------------------------------------------

class ReplyLogInputsOnly():
  "Read & verify log"
  def __init__( self, filename ):
    print "ReplyLogInputOnly", filename
    self._logFile = open( filename, "rb" )

  def read( self, numChars ):
    s = []
    for i in range(numChars):
      while( self._logFile.read(1) not in [chr(0x01), ''] ):
        c = self._logFile.read(1) # skip write output
        if not c:
          raise LogEnd()
        assert( i == 0 ) # the packets should be complete
      s.append(self._logFile.read(1))
      if not s[-1]:
        raise LogEnd()
    return ''.join(s)

  def write( self, chars ):
    pass 
  
#-------------------------------------------------------------------

