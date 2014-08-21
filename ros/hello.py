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

def publisherUpdate(caller_id, topic, publishers):
    return (1, "Hi", 42)

master = ServerProxy( ROS_MASTER_URI )
code, statusMessage, systemState = master.getSystemState('/')
assert code == 1, code
assert len(systemState) == 3, systemState
print "Publishers:"
for s in systemState[0]:
  print s

caller_id = "hello_test_client"
topic = "/hello"
topic_type = "std_msgs/String"
caller_api = MY_CLIENT_URI # for "publisherUpdate"
print master.registerSubscriber(caller_id, topic, topic_type, caller_api)

#-------------------------------------------------------------------
# vim: expandtab sw=4 ts=4

