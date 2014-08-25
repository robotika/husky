"""
  Python client to ROS example
    http://robohub.org/ros-101-a-practical-example/
  without need of ROS installation
"""

# on server side:
# terminalA:   roscore
# terminalB:   rostopic pub /hello std_msgs/String "Hello Robot"

#ROS_MASTER_URI = 'http://192.168.0.13:11311'
ROS_MASTER_URI = 'http://192.168.1.11:11311'

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
#topic, topic_type, md5 = "/hello", "std_msgs/String", '992ce8a1687cec8c8bd883ec73ca41d1'
#topic = "/imu/data"
#topic = "/husky/data/encoders"
#topic_type = "std_msgs/Imu"
#topic_type = "clearpath_base/Encoders", 
#topic, topic_type, md5 = "/husky/data/power_status", 'clearpath_base/PowerStatus', 'f246c359530c58415aee4fe89d1aca04'
#topic, topic_type, md5 = '/husky/data/safety_status', 'clearpath_base/SafetyStatus', 'cf78d6042b92d64ebda55641e06d66fa'
topic, topic_type, md5 = '/joy', 'sensor_msgs/Joy', '5a9ea5f83505693b71e785041e67a8bb'

caller_api = MY_CLIENT_URI # for "publisherUpdate"

code, statusMessage, topicTypes = master.getTopicTypes(caller_id)
assert code == 1, code
print "---"
print "topicTypes:"
for t in topicTypes:
    print t
print "---"

code, statusMessage, publishers = master.registerSubscriber(caller_id, topic, topic_type, caller_api)
assert code == 1, code
assert len(publishers) == 1, publishers # i.e. fails if publisher is not ready now

print publishers
publisher = ServerProxy( publishers[0].replace("martind-ThinkPad-R60", "192.168.0.13") ) # "pseudo DNS"
code, statusMessage, protocolParams = publisher.requestTopic( caller_id, topic, [["TCPROS"]] )
assert code == 1, code
assert len(protocolParams) == 3, protocolParams

print protocolParams
#hostPortPair = ( "192.168.33.105", protocolParams[2] )
hostPortPair = ( protocolParams[1], protocolParams[2] )
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP


soc.connect( hostPortPair )
soc.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
soc.setblocking(0)

soc.settimeout( 30.0 )

header = prefix4BytesLen(
        prefix4BytesLen( "callerid=/hello_test_client" ) +
        prefix4BytesLen( "topic="+topic ) +
        prefix4BytesLen( "type="+topic_type ) +
#        prefix4BytesLen( "md5sum=992ce8a1687cec8c8bd883ec73ca41d1" ) + # hello
#        prefix4BytesLen( "md5sum=6a62c6daae103f4ff57a132d6f95cec2" ) + # imu
#        prefix4BytesLen( "md5sum=2ea748832c2014369ffabd316d5aad8c" ) + # Encoders
        prefix4BytesLen( "md5sum="+md5 ) +
        "" )


soc.send( header )
f = open("tmp.bin","wb")
for i in xrange(10):
    print "--------------------"
    data = soc.recv(4)
    f.write( data )
    size = struct.unpack("I", data)[0]
    print "SIZE", size
    data = soc.recv( size )
    f.write( data )
    f.flush()
    for s in splitLenStr(data):
        print s
f.close()

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

