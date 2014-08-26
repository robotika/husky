import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

def publisherUpdate(caller_id, topic, publishers):
#def publisherUpdate( data ):
    print "called 'publisherUpdate' with", data
    return (1, "Hi", 42)

def requestTopic(caller_id, topic, publishers):
    print "REQ", (caller_id, topic, publishers)
    return 1, "ready on martind-blabla", ['TCPROS', '192.168.0.12', 8123]

server = SimpleXMLRPCServer(("192.168.0.12", 8000))
print "Listening on port 8000..."
server.register_function(publisherUpdate, "publisherUpdate")
server.register_function(requestTopic, "requestTopic")
server.serve_forever()

# vim: expandtab sw=4 ts=4

