import xmlrpclib
import base64

SERVER_IP       = "0.0.0.0"
PORT            = 6969

server = xmlrpclib.ServerProxy('http://localhost:6969')
print 'Ping:', server.ping()

with open('arial.ttf', 'rb') as f:
    data = f.read()
    print 'Fuzz:', server.send_font(base64.b64encode(data))