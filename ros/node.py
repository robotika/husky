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
import os

from threading import Thread

from tcpros import prefix4BytesLen, Tcpros, LoggedStream, ReplayLoggedStream
from msgs import * # including lookupTopicType

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
    def __init__( self, subscribe=[], publish=[], heartbeat=None, filename=None, replay=False, assertWrite=True ):
        self.callerId = '/node_test_ros' # TODO combination host/port?
        self.heartbeat = heartbeat
        if not replay:
            if filename is None:
                dt = datetime.datetime.now()
                filename = "meta" + dt.strftime("%y%m%d_%H%M%S.log") 
            self.metalog = open( filename, "wb" )
            self.callerApi = "http://"+NODE_HOST+":%d" % NODE_PORT
            print "STARTING", self.callerId, "at", self.callerApi
            self.server = MyXMLRPCServer( (NODE_HOST, NODE_PORT) )
            self.master = ServerProxy( ROS_MASTER_URI )
        else:
            self.callerApi = None # replay log file(s)
            self.metalog = open( filename, "rb" )
            self.metalogDir = os.path.dirname( filename )

        self.sockets = {}
        for topic in subscribe:
            if self.callerApi != None: # or special bool for that?
                logStream = LoggedStream( self.requestTopic( topic ).recv, prefix=topic.replace('/','_') )
                self.metalog.write( logStream.filename + '\n' )
            else:
                filename = self.metalog.readline().strip()
                logStream = ReplayLoggedStream( self.metalogDir + os.sep + filename, assertWrite=assertWrite )
            self.sockets[topic] = Tcpros( readMsgFn=logStream.readMsg )

        self.publishSockets = {}
        for topic in publish:
            if self.callerApi != None:
                self.publishSockets[topic] = LoggedStream( writeFn=self.publishTopic( topic ).send, prefix=topic.replace('/','_') )
                self.metalog.write( self.publishSockets[topic].filename + '\n' )
            else:
                filename = self.metalog.readline().strip()
                self.publishSockets[topic] = ReplayLoggedStream( self.metalogDir + os.sep + filename, assertWrite )
        self.cmdList = []


    def requestTopic( self, topic ):
        code, statusMessage, publishers = self.master.registerSubscriber(self.callerId, topic, lookupTopicType(topic)[0], self.callerApi)
        assert code == 1, (code, statusMessage)
        assert len(publishers) == 1, (topic, publishers) # i.e. fails if publisher is not ready now
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
            prefix4BytesLen( "type="+lookupTopicType(topic)[0] ) +
            prefix4BytesLen( "md5sum="+lookupTopicType(topic)[1] ) +
            "" )
        soc.send( header )
        return soc

    def publishTopic( self, topic ):
        "establish connection with exactly one subscriber"
        print "PUBLISH", topic, ( self.callerId, topic, lookupTopicType(topic)[0], self.callerApi )
        code, statusMessage, subscribers = self.master.registerPublisher( self.callerId, topic, lookupTopicType(topic)[0], self.callerApi )
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
            prefix4BytesLen( "type="+lookupTopicType(topic)[0] ) +
            prefix4BytesLen( "md5sum="+lookupTopicType(topic)[1] ) +
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
            self.publishSockets[topic].writeMsg( lookupTopicType(topic)[3]( *cmd ) ) # 4th param is packing function
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
                        ret.append( (topic,lookupTopicType(topic)[2]( m )) )
                        if self.heartbeat == None or topic == self.heartbeat:
                            atLeastOne = True
            else:
                topic = self.metalog.readline().strip()
                if topic == '---':
                    atLeastOne = True
                    break
                soc = self.sockets[ topic ]
                m = soc.readMsg()
                ret.append( (topic,lookupTopicType(topic)[2]( m )) )
        if self.callerApi != None:
            self.metalog.write( '---\n' )
            self.metalog.flush()
        return ret


def testNode0( metalog ):
    node = NodeROS(subscribe=['/X1/cmd_vel'])
    node.update()

def testNode(metalog):
    node = NodeROS(subscribe=[], publish=['/X1/cmd_vel'])
    for i in xrange(1000):
        node.cmdList.append(('/X1/cmd_vel', (-0.5, 0.0)))
        node.update()
        time.sleep(0.05)

def testNode2( metalog ):
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

