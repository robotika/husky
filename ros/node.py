"""
  Python code imitating ROS node (both publisher and subscriber)
  targeted to control Husky platform.
  usage:
      ./node.py <node IP> <master IP>
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


from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer

import socket
import struct
import sys
import time
import datetime

from threading import Thread

from tcpros import prefix4BytesLen, Tcpros, LoggedStream
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
    def __init__( self, subscribe=[], publish=[] ):
        dt = datetime.datetime.now()
        filename = "meta" + dt.strftime("%y%m%d_%H%M%S.log") 
        self.metalog = open( filename, "wb" )
        self.callerId = '/node_test_ros' # TODO combination host/port?
        self.callerApi = "http://"+NODE_HOST+":%d" % NODE_PORT
        print "STARTING", self.callerId, "at", self.callerApi # TODO logging instead
        self.server = MyXMLRPCServer( (NODE_HOST, NODE_PORT) )
        self.master = ServerProxy( ROS_MASTER_URI )
        self.sockets = {}
        for topic in subscribe:
            self.sockets[topic] = Tcpros( readMsgFn=LoggedStream( self.requestTopic( topic ).recv, prefix=topic.replace('/','_') ).readMsg )
        self.publishSockets = {}
        for topic in publish:
            self.publishSockets[topic] = LoggedStream( writeFn=self.publishTopic( topic ).send, prefix=topic.replace('/','_') )
        self.cmdList = []

    def lookupTopicType( self, topic ):
        # TODO separate msgs.py with types and md5
        tab = { 
                '/hello': ("std_msgs/String", '992ce8a1687cec8c8bd883ec73ca41d1', parseString, packString),
                '/imu/data': ("std_msgs/Imu", "6a62c6daae103f4ff57a132d6f95cec2", parseImu),
                '/husky/data/encoders': ("clearpath_base/Encoders", '2ea748832c2014369ffabd316d5aad8c', parseEncoders),
                '/husky/data/power_status': ('clearpath_base/PowerStatus', 'f246c359530c58415aee4fe89d1aca04', parsePower),
                '/husky/data/safety_status': ('clearpath_base/SafetyStatus', 'cf78d6042b92d64ebda55641e06d66fa', parseNone), # TODO
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
        for topic in self.publishSockets.keys():
            code, statusMessage, numUnreg = self.master.unregisterPublisher( self.callerId, topic, self.callerApi )
            print code, statusMessage, numUnreg


    def update( self ):
        for topic, cmd in self.cmdList:
            self.metalog.write( topic + '\n' )
            self.metalog.flush()
            self.publishSockets[topic].writeMsg( self.lookupTopicType(topic)[3]( cmd ) ) # 4th param is packing function
        self.cmdList = []
        atLeastOne = False
        while not atLeastOne and len(self.sockets) > 0:
            for topic,soc in self.sockets.items():
                m = soc.readMsg()
                if m != None:
                    self.metalog.write( topic + '\n' )
                    self.metalog.flush()
                    print topic
                    print self.lookupTopicType(topic)[2]( m )
                    atLeastOne = True


def testNode1():
    node = NodeROS( subscribe=['/hello'])
    node.update()

def testNode2():
    node = NodeROS( subscribe=['/imu/data', '/husky/data/encoders', '/husky/data/power_status',
        '/husky/data/safety_status', '/joy'])
    for i in xrange(1000):
        node.update()

def testNode():
    node = NodeROS( publish=['/hello'])
    node.cmdList.append( ('/hello', "Hello ROS Universe!") )
    node.update()
    assert len(node.cmdList) == 0, node.cmdList
    node.unregisterAll()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print __doc__
        sys.exit(1)
    NODE_HOST = sys.argv[1]
    ROS_MASTER_URI = 'http://'+sys.argv[2]+':11311'
    testNode()

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

