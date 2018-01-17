import asyncore
import logging
import socket
import threading
from PyQt5 import QtCore
from io import StringIO


class TCPClient(asyncore.dispatcher):

    address = ()
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockThread = threading.Thread(target=asyncore.loop)


    def connectSocket(self,IP, Port):
        self.url = IP
        self.logger = logging.getLogger(self.url)
        self.write_buffer = 'hellow'
        self.read_buffer = StringIO()
        self.address = (IP, Port)
        self.logger.debug('connecting to %s', self.address)
        try:
            self.connect(self.address)
            self.sockThread.start()
            return 1
        except:
            return 0

    def handle_error(self):
        pass
"""
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)s: %(message)s',
                        )

    # clients = [
    #     HttpClient('192.168.10.26'),
    #     HttpClient('192.168.10.27'),
    # ]
    clients = [
        TCPClient('192.168.10.26', 8000),
        TCPClient('192.168.10.26', 8000),
        TCPClient('192.168.10.26', 8000)
    ]
    logging.debug('LOOP STARTING')

    asyncore.loop()

    logging.debug('LOOP DONE')

    for c in clients:
        response_body = c.read_buffer.getvalue()
        print(c.url, 'got', len(response_body), 'bytes')
"""