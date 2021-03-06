from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from struct import pack
import sys
import socket, json

sys.path[0:0] = ["util/"]
from StanceClassifier.util import Util, path_from_root


class StanceClassifier:

    # Initialize the classifier handler:
    def __init__(self, host, port):
        self.port = port
        self.host = host

    # classify a stance:
    def classify(self, parameters):
        # Create a classification request for local stance classifier server in json format:
        aux = json.loads(parameters.decode('utf-8'))
        info = {}
        info['original'] = aux["original"]
        info['reply'] = aux["reply"]
        data = json.dumps(info)
        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            print("Sending data in batches...")
            length = pack('>Q', len(data.encode('utf-8')))
            s.sendall(length)
            s.sendall(data.encode('utf-8'))
            ack = s.recv(1)
            if ack == b'\x00':
                print("Data sent successfully.")
            response = json.loads(s.recv(1024).decode('utf-8'))
            s.close()

            return response
        except Exception as exc:
            return {'Error': ['Error while classifying a stance.']}


# This class represents the Stance Classifier server handler:
class StanceClassifierServer(HTTPServer, object):

    # Initialize the server:
    def __init__(self, *args, **kwargs):
        super(StanceClassifierServer, self).__init__(*args, **kwargs)
        self.cs = None

    # Add a classifier:
    def addStanceClassifier(self, sc):
        self.cs = sc


# This class represents the Local Stance Classifier server handler:
class StanceClassifierHandler(BaseHTTPRequestHandler):

    # Handler for the POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(post_data)
        parameters = self.parse_parameters(post_data)
        print(parameters)
        if 'Error' not in str(parameters):
            output_parameters = self.classify(parameters)
            print(output_parameters)
            self.respond(output_parameters)
        else:
            self.respond(parameters)
        return

    # Send a classification result back to the requester:
    def respond(self, parameters):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response = json.dumps(parameters)
        self.wfile.write(response.encode('utf-8'))
        return

    def classify(self, parameters):
        return self.server.cs.classify(parameters)

    def parse_parameters(self, text):
        parameters = text

        if '"original":' not in str(text) or '"reply":' not in str(text):
            parameters = {'Error': ['Parameters "source" or "reply" missing']}
        return parameters

class StanceClassifierHTTPServerRunner:

    def run(self):
        try:
            util = Util()
            configurations = util.loadResources(path_from_root('configurations.txt'))
            SERVER_PORT_NUMBER = int(configurations['main_server_port'])
            LOCAL_SERVER = configurations['local_server_hostname']
            LOCAL_PORT_NUMBER = int(configurations['local_server_port'])

            cs = StanceClassifier(LOCAL_SERVER, LOCAL_PORT_NUMBER)
            server = StanceClassifierServer(('', SERVER_PORT_NUMBER), StanceClassifierHandler)
            server.addStanceClassifier(cs)
            print("Bound to " + LOCAL_SERVER + ":" + str(SERVER_PORT_NUMBER) + ". Listening for connections")
            server.serve_forever()


        except KeyboardInterrupt:
            server.socket.close()
