"""
  Python client to ROS example
    http://robohub.org/ros-101-a-practical-example/
  without need of ROS installation
"""

# on server side:
# terminalA:   roscore
# terminalB:   rostopic pub /hello std_msgs/String "Hello Robot"

ROS_MASTER_URI = 'http://192.168.33.105:11311'

MY_CLIENT_URI = 'http://192.168.33.100:8000'

from xmlrpclib import ServerProxy
import socket
import struct
import sys

def prefix4BytesLen( s ):
    "adding ROS length"
    return struct.pack("I", len(s)) + s

def splitLenStr( data ):
    ret = []
    while len(data) >= 4:
        size = struct.unpack( "I", data[:4] )[0]
        data = data[4:]
        ret.append( data[:size] )
        data = data[size:]
    return ret

master = ServerProxy( ROS_MASTER_URI )
code, statusMessage, systemState = master.getSystemState('/')
assert code == 1, code
assert len(systemState) == 3, systemState
print "Publishers:"
for s in systemState[0]:
  print s

caller_id = "/hello_test_client"
topic = "/hello"
topic_type = "std_msgs/String"
caller_api = MY_CLIENT_URI # for "publisherUpdate"

code, statusMessage, topicTypes = master.getTopicTypes(caller_id)
assert code == 1, code
print "---"
print "topicTypes:"
print topicTypes
print "---"

code, statusMessage, publishers = master.registerSubscriber(caller_id, topic, topic_type, caller_api)
assert code == 1, code
assert len(publishers) == 1, publishers # i.e. fails if publisher is not ready now

publisher = ServerProxy( publishers[0].replace("martind-ThinkPad-R60", "192.168.33.105") ) # "pseudo DNS"
code, statusMessage, protocolParams = publisher.requestTopic( caller_id, topic, [["TCPROS"]] )
assert code == 1, code
assert len(protocolParams) == 3, protocolParams

hostPortPair = ( "192.168.33.105", protocolParams[2] )
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP


soc.connect( hostPortPair )
soc.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
soc.setblocking(0)

soc.settimeout( 3.0 )

header = prefix4BytesLen(
        prefix4BytesLen( "callerid=/hello_test_client" ) +
        prefix4BytesLen( "topic=/hello" ) +
        prefix4BytesLen( "type=std_msgs/String" ) +
        prefix4BytesLen( "md5sum=992ce8a1687cec8c8bd883ec73ca41d1" ) +
        "" )


soc.send( header )
while 1:
    print "--------------------"
    data = soc.recv(4)
    size = struct.unpack("I", data)[0]
    print "SIZE", size
    data = soc.recv( size )
    for s in splitLenStr(data):
        print s


#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

