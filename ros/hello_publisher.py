"""
  Python client/publisher imitating ROS example
    http://robohub.org/ros-101-a-practical-example/
  without need of ROS installation
"""

# on server side:
# terminalA:   roscore
# terminalB:   rostopic pub /hello std_msgs/String "Hello Robot"
# terminalC:   rostopic echo /hello
# ... here we will try to imitate node from terminalB


#ROS_MASTER_URI = 'http://192.168.0.13:11311'
ROS_MASTER_URI = 'http://192.168.1.11:11311'

#MY_CLIENT_URI = 'http://192.168.0.12:8000'
MY_CLIENT_URI = 'http://192.168.1.42:8000'

#HOST = '192.168.0.12'
HOST = '192.168.1.42'
PORT = 8123

from xmlrpclib import ServerProxy
import socket
import struct
import sys
import time

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

caller_id = "/hello_node"
#topic, topic_type, md5 = "/hello", "std_msgs/String", '992ce8a1687cec8c8bd883ec73ca41d1'
topic, topic_type, md5 = "/husky/cmd_vel", "geometry_msgs/Twist", '9f195f881246fdfa2798d1d3eebca84a'

caller_api = MY_CLIENT_URI # for "publisherUpdate"

code, statusMessage, subscribers = master.registerPublisher(caller_id, topic, topic_type, caller_api)
print subscribers

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((HOST, PORT))
serverSocket.listen(1)
socket, addr = serverSocket.accept() 
print 'Connected by', addr
data = socket.recv(1024)
print data
print "LEN", len(data)

header = prefix4BytesLen(
        prefix4BytesLen( "callerid="+caller_id ) +
        prefix4BytesLen( "topic="+topic ) +
        prefix4BytesLen( "type="+topic_type ) +
        prefix4BytesLen( "md5sum="+md5 ) +
        "" )
socket.send( header )
data = prefix4BytesLen(
        struct.pack("dddddd", 0.1,0,0, 0,0,0)
        )
socket.send( data )
time.sleep(1.0)
data = prefix4BytesLen(
        struct.pack("dddddd", 0.0,0,0, 0,0,0)
        )
socket.send( data )

code, statusMessage, numUnreg = master.unregisterPublisher(caller_id, topic, caller_api)
print code, statusMessage, numUnreg

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

