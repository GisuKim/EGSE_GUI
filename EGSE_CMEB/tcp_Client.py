import asyncore
import logging
import socket
import threading
import time
from PyQt5 import QtCore
from io import StringIO

class CMEBClient(asyncore.dispatcher):

    address = ()
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.write_buffer = 'hellow'
        self.read_buffer = StringIO()
        self.sockThread = threading.Thread(target=asyncore.loop)
        self.sockThread.start()
        # self.logger.debug('CMEB OPEN')

    def connectSocket(self,IP, Port):
        print("CMEB Connect into")
        url = IP
        self.logger = logging.getLogger(url)
        address = (IP, Port)
        self.logger.debug('connecting to %s', address)
        self.connect(address)

    def handle_expt(self):
        print("expt")

    def handle_error(self):
        print("err")

    def handle_read(self):
        pass

    def handle_connect(self):
        self.write_buffer = "cmeb connect"
        sent = self.send(self.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]

class TCPClient(asyncore.dispatcher):

    address = ()
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.write_buffer = 'hellow'
        self.read_buffer = StringIO()
        self.sockThread = threading.Thread(target=asyncore.loop)
        self.sockThread.start()
        # self.logger.debug('EGSE OPEN')

    def connectSocket(self,IP, Port):
        url = IP
        self.logger = logging.getLogger(url)
        address = (IP, Port)
        self.logger.debug('connecting to %s', address)
        self.connect(address)

    def handle_expt(self):
        print("expt")

    def handle_error(self):
        print("err")

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