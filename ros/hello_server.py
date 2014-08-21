import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

def publisherUpdate(caller_id, topic, publishers):
    return (1, "Hi", 42)

server = SimpleXMLRPCServer(("192.168.33.100", 8000))
print "Listening on port 8000..."
server.register_function(publisherUpdate, "publisherUpdate")
server.serve_forever()

# vim: expandtab sw=4 ts=4

