import socket
import json
import sys
from os import getcwd
from struct import unpack
from StanceClassifier.stance_classifier import StanceClassifier
from StanceClassifier.util import Util, path_from_root

class StanceClassifierTCPServerRunner:

    def run(self):

        #Load configurations
        util = Util()
        configurations = util.loadResources(path_from_root('configurations.txt'))

        model = configurations['model']


        hostname = configurations['local_server_hostname']
        port = int(configurations['local_server_port'])


        print("*** Starting Local Stance Classifier server ***")
        stance_classifier = StanceClassifier(model)
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((hostname, port))
        serversocket.listen(5)
        print("Local Stance Classifier server ready!")
        print("Bound to " + hostname + ":" + str(port) + ". Listening for connections")

        #Upon receival of classification request, do:
        while 1:

            try:
                #Open connection:
                (conn, address) = serversocket.accept()

                print("*** Incoming connection from " + str(address))

                print('*** Receiving data in batches of 4096 bytes...')
                bs = conn.recv(8)
                (length,) = unpack('>Q', bs)
                print('*** Data length (bytes): ' + str(length))
                data = b''
                c = 1
                while len(data) < length:
                    #print('Receiving batch %d ...' % c)
                    to_read = length - len(data)
                    data += conn.recv(4096 if to_read > 4096 else to_read)
                    c += 1
                assert len(b'\00') == 1
                conn.sendall(b'\00')

                source = json.loads(data)['original']
                reply = json.loads(data)['reply']

                output = stance_classifier.classify(source, reply)

                data = {}
                data['class'] = output[0]
                data['probs'] = {}
                for i in range(0, len(output[1])):
                    data['probs'][i] = output[1][i]

                print("Sending... " + str(data))
                conn.send(json.dumps(data).encode('utf-8'))
                conn.close()
            except Exception as ex:
                print(ex)



