"""
  Python code imitating ROS node (both publisher and subscriber)
  targeted to control Husky platform.
  usage:
      ./node.py [<node IP> <master IP> | <metalog>]
"""

# for test run on server:
# terminalA:   roscore
# terminalB:   rostopic pub /hello std_msgs/String "Hello Robot"
# terminalC:   rostopic echo /hello

SOCKET_TIMEOUT = 0.0

#ROS_MASTER_URI = 'http://192.168.1.11:11311'
#ROS_MASTER_URI = 'http://192.168.0.13:11311'
ROS_MASTER_URI = None

#NODE_HOST, NODE_PORT = ("192.168.1.42", 8000)
#NODE_HOST, NODE_PORT = ("192.168.0.12", 8000)
NODE_HOST, NODE_PORT = (None, 8000)
PUBLISH_PORT = 8123

def setIPs( nodeIP, masterIP ):
    global ROS_MASTER_URI
    global NODE_HOST
    ROS_MASTER_URI = masterIP
    NODE_HOST = nodeIP


from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer

import socket
import struct
import sys
import time
import datetime

from threading import Thread

from tcpros import prefix4BytesLen, Tcpros, LoggedStream, ReplayLoggedStream
from msgs import *

def publisherUpdate(caller_id, topic, publishers):
    print "called 'publisherUpdate' with", (caller_id, topic, publishers)
    return (1, "Hi, I am fine", 42) # (code, statusMessage, ignore) 

def requestTopic(caller_id, topic, publishers):
    print "REQ", (caller_id, topic, publishers)
    return 1, "ready on martind-blabla", ['TCPROS', NODE_HOST, PUBLISH_PORT]


class MyXMLRPCServer( Thread ):
    def __init__( self, nodeAddrHostPort ):
        Thread.__init__( self )
        self.setDaemon( True )
        self.server = SimpleXMLRPCServer( nodeAddrHostPort )
        print "Listening on port %d ..." % nodeAddrHostPort[1]
        self.server.register_function(publisherUpdate, "publisherUpdate")
        self.server.register_function(requestTopic, "requestTopic")
        self.start()

    def run( self ):
        self.server.serve_forever()


class NodeROS:
    def __init__( self, subscribe=[], publish=[], heartbeat=None, metalog=None ):
        self.callerId = '/node_test_ros' # TODO combination host/port?
        self.heartbeat = heartbeat
        if metalog == None:
            dt = datetime.datetime.now()
            filename = "meta" + dt.strftime("%y%m%d_%H%M%S.log") 
            self.metalog = open( filename, "wb" )
            self.callerApi = "http://"+NODE_HOST+":%d" % NODE_PORT
            print "STARTING", self.callerId, "at", self.callerApi
            self.server = MyXMLRPCServer( (NODE_HOST, NODE_PORT) )
            self.master = ServerProxy( ROS_MASTER_URI )
        else:
            self.callerApi = None # replay log file(s)
            self.metalog = open( metalog, "rb" )

        self.sockets = {}
        for topic in subscribe:
            if self.callerApi != None: # or special bool for that?
                logStream = LoggedStream( self.requestTopic( topic ).recv, prefix=topic.replace('/','_') )
                self.metalog.write( logStream.filename + '\n' )
            else:
                filename = self.metalog.readline().strip()
                logStream = ReplayLoggedStream( filename )
            self.sockets[topic] = Tcpros( readMsgFn=logStream.readMsg )

        self.publishSockets = {}
        for topic in publish:
            if self.callerApi != None:
                self.publishSockets[topic] = LoggedStream( writeFn=self.publishTopic( topic ).send, prefix=topic.replace('/','_') )
                self.metalog.write( self.publishSockets[topic].filename + '\n' )
            else:
                filename = self.metalog.readline().strip()
                self.publishSockets[topic] = ReplayLoggedStream( filename )
        self.cmdList = []


    def lookupTopicType( self, topic ):
        # TODO separate msgs.py with types and md5
        tab = { 
                '/hello': ("std_msgs/String", '992ce8a1687cec8c8bd883ec73ca41d1', parseString, packString),
                '/imu/data': ("std_msgs/Imu", "6a62c6daae103f4ff57a132d6f95cec2", parseImu),
                '/husky/data/encoders': ("clearpath_base/Encoders", '2ea748832c2014369ffabd316d5aad8c', parseEncoders),
                '/husky/data/power_status': ('clearpath_base/PowerStatus', 'f246c359530c58415aee4fe89d1aca04', parsePower),
                '/husky/data/safety_status': ('clearpath_base/SafetyStatus', 'cf78d6042b92d64ebda55641e06d66fa', parseNone), # TODO
                '/husky/data/system_status': ('clearpath_base/SystemStatus', 'b24850c808eb727058fff35ba598006f', parseNone), # TODO
                '/husky/cmd_vel' : ('geometry_msgs/Twist', '9f195f881246fdfa2798d1d3eebca84a', parseNone, packCmdVel),
                '/joy': ('sensor_msgs/Joy', '5a9ea5f83505693b71e785041e67a8bb', parseJoy),
              }       
        return tab[topic]


    def requestTopic( self, topic ):
        code, statusMessage, publishers = self.master.registerSubscriber(self.callerId, topic, self.lookupTopicType(topic)[0], self.callerApi)
        assert code == 1, (code, statusMessage)
        assert len(publishers) == 1, publishers # i.e. fails if publisher is not ready now
        print publishers
        publisher = ServerProxy( publishers[0] )
        code, statusMessage, protocolParams = publisher.requestTopic( self.callerId, topic, [["TCPROS"]] )
        assert code == 1, (code, statusMessage)
        assert len(protocolParams) == 3, protocolParams
        print code, statusMessage, protocolParams
        hostPortPair = ( protocolParams[1], protocolParams[2] )
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
        soc.connect( hostPortPair )
        soc.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        soc.setblocking(0)
        soc.settimeout( SOCKET_TIMEOUT )
        header = prefix4BytesLen(
            prefix4BytesLen( "callerid="+self.callerId ) +
            prefix4BytesLen( "topic="+topic ) +
            prefix4BytesLen( "type="+self.lookupTopicType(topic)[0] ) +
            prefix4BytesLen( "md5sum="+self.lookupTopicType(topic)[1] ) +
            "" )
        soc.send( header )
        return soc

    def publishTopic( self, topic ):
        "establish connection with exactly one subscriber"
        print "PUBLISH", topic, ( self.callerId, topic, self.lookupTopicType(topic)[0], self.callerApi )
        code, statusMessage, subscribers = self.master.registerPublisher( self.callerId, topic, self.lookupTopicType(topic)[0], self.callerApi )
        print subscribers

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSocket.bind((NODE_HOST, PUBLISH_PORT))
        print "Waiting ..."
        serverSocket.listen(1)
        soc, addr = serverSocket.accept() 
        print 'Connected by', addr
        data = soc.recv(1024) # TODO properly load and parse/check
        print data
        print "LEN", len(data)
        header = prefix4BytesLen(
            prefix4BytesLen( "callerid="+self.callerId ) +
            prefix4BytesLen( "topic="+topic ) +
            prefix4BytesLen( "type="+self.lookupTopicType(topic)[0] ) +
            prefix4BytesLen( "md5sum="+self.lookupTopicType(topic)[1] ) +
            "" )
        soc.send( header )
        return soc


    def unregisterAll( self ):
        if self.callerApi == None:
            return # only logs
        for topic in self.publishSockets.keys():
            code, statusMessage, numUnreg = self.master.unregisterPublisher( self.callerId, topic, self.callerApi )
            print code, statusMessage, numUnreg


    def update( self ):
        for topic, cmd in self.cmdList:
            if self.callerApi != None:
                self.metalog.write( topic + '\n' )
                self.metalog.flush()
            else:
                logTopic = self.metalog.readline().strip()
                assert topic == logTopic, (topic, logTopic)
            self.publishSockets[topic].writeMsg( self.lookupTopicType(topic)[3]( *cmd ) ) # 4th param is packing function
        self.cmdList = []
        atLeastOne = False
        ret = []
        while not atLeastOne and len(self.sockets) > 0:
            if self.callerApi != None:
                for topic,soc in self.sockets.items():
                    m = soc.readMsg()
                    if m != None:
                        self.metalog.write( topic + '\n' )
                        self.metalog.flush()
                        ret.append( (topic,self.lookupTopicType(topic)[2]( m )) )
                        if self.heartbeat == None or topic == self.heartbeat:
                            atLeastOne = True
            else:
                topic = self.metalog.readline().strip()
                if topic == '---':
                    atLeastOne = True
                    break
                soc = self.sockets[ topic ]
                m = soc.readMsg()
                ret.append( (topic,self.lookupTopicType(topic)[2]( m )) )
        if self.callerApi != None:
            self.metalog.write( '---\n' )
            self.metalog.flush()
        return ret


def testNode1( metalog ):
    node = NodeROS( subscribe=['/hello'], metalog=metalog )
    node.update()

def testNode( metalog ):
    node = NodeROS( subscribe=['/imu/data', '/husky/data/encoders', '/husky/data/power_status',
        '/husky/data/safety_status', '/joy', '/husky/data/system_status'], 
        publish=['/husky/cmd_vel'],
        heartbeat='/husky/data/encoders',
        metalog=metalog)
    for i in xrange(100):
        node.cmdList.append( ('/husky/cmd_vel', (0.1,0)) )
        node.update()
    node.cmdList.append( ('/husky/cmd_vel', (0,0)) )
    node.update()

def testNode3( metalog ):
    node = NodeROS( publish=['/hello'], metalog=metalog )
    node.cmdList.append( ('/hello', "Hello ROS Universe!") )
    node.update()
    assert len(node.cmdList) == 0, node.cmdList
    node.unregisterAll()

if __name__ == "__main__":
    if len(sys.argv) < 2 or (len(sys.argv)==2 and "meta" not in sys.argv[1]):
        print __doc__
        sys.exit(1)

    metalog = None
    if "meta" in sys.argv[1]:
        metalog = sys.argv[1]
    else:
        NODE_HOST = sys.argv[1]
        ROS_MASTER_URI = 'http://'+sys.argv[2]+':11311'
    testNode( metalog )

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

