import asyncore
import logging
import socket
import threading
import cv2
import numpy as np

import time
from PyQt5 import QtCore
from io import StringIO


FRAME_WIDTH = 2048
FRAME_HEIGHT = 2048
CHANNEL = 2       #16BIT BGR565
IMAGE_SIZE = FRAME_WIDTH * FRAME_HEIGHT * CHANNEL

## Mode Define
MODE_MESSAGE_READ = 0
MODE_CBIT_READ = 1
MODE_IMAGE_READ = 2

class CMEBClient(asyncore.dispatcher):

    address = ()
    control = None
    mainWindow = None
    imageReadCNT = 0
    receiveImage = b''

    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.write_buffer = b''
        self.read_buffer = StringIO()
        self.sockThread = threading.Thread(target=asyncore.loop)
        self.sockThread.start()
        self.readMode = MODE_MESSAGE_READ
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
        print("cmeb soecket err")

    def socketToNumpy(self, cameraFeed, sockData):
        k = 2
        j = cameraFeed.shape[1]
        i = cameraFeed.shape[0]
        sockData = np.fromstring(sockData, np.uint8)
        cameraFeed = np.tile(sockData, 1).reshape((i, j, k))

        return cameraFeed

    def handle_read(self):
        data = self.recv(8192)
        self.logger.debug('handle_read() -> %d bytes', len(data))
        self.logger.debug('mode : %d', self.readMode)
        if self.readMode == MODE_MESSAGE_READ:
            if data.decode() == "RX_IMAGE":  # Image 전송요청 회신시
                self.ImageSendStart()  # Image 전송!
            elif data.decode() == "RE_RX_IMAGE":
                self.imageReadCNT = 0
                print('클리 됐냐 ? %d', self.imageReadCNT)
                self.readMode = MODE_IMAGE_READ
            elif data.decode() == "SSR_ON":
                self.isSSR = True
                self.btn_CMEB_Power.setText("Power OFF")
                self.SetConsoleMessage(str(self.address) + ' ' + 'SSR_ON')
            elif data.decode() == "SSR_OFF":
                self.isSSR = False
                self.btn_CMEB_Power.setText("Power ON")
                self.SetConsoleMessage(str(self.address) + ' ' + 'SSR_OFF')
            elif data.decode() == "REQ_CAM_START":
                self.SetConsoleMessage(str(self.address) + ' ' + 'REQ_CAM_START')
            elif data.decode() == "GET_RESULT_IMAGE":
                self.SetConsoleMessage(str(self.address) + ' ' + 'GET_RESULT_IMAGE')
            elif data.decode() == "GET_FPA_STATUS":
                self.SetConsoleMessage(str(self.address) + ' ' + 'GET_FPA_STATUS')
            else:
                self.logger.debug('Error')
        elif self.readMode == MODE_CBIT_READ:
            # self.logger.debug('MODE_CBIT_READ')
            # self.logger.debug(data)
            self.SetCmebStatusUI(data)
            self.readMode = MODE_MESSAGE_READ
        elif self.readMode == MODE_IMAGE_READ:
            print('진입 데이타 길이는 %d', self.imageReadCNT)
            if self.imageReadCNT < IMAGE_SIZE:
                if len(data) > 0:
                    self.receiveImage += data
                    self.imageReadCNT += len(data)
                    self.logger.debug('read image size : %d  -- read size : %d', IMAGE_SIZE, self.imageReadCNT)
                    self.mainWindow.progressBar.setValue((self.imageReadCNT/IMAGE_SIZE)*100)
                    self.mainWindow.statusBar().showMessage('CMEB -> PC Image Sending..')
                    if (self.imageReadCNT == IMAGE_SIZE):
                        self.mainWindow.statusBar().showMessage('CMEB -> PC Send Complet')
                        print(self.imageReadCNT)
                        self.readMode = MODE_MESSAGE_READ
                        self.imageReadCNT = 0
                        img = self.control.DataToImage(self.receiveImage)
                        self.receiveImage = b''
                        img = cv2.resize(img, None, fx=1, fy=1, interpolation=cv2.INTER_CUBIC)
                        frame  ={}
                        frame["img"] = img
                        self.control.ImgReturn.setImage(self.control.image_Transfrom(frame))

    def handle_connect(self):
        self.mainWindow.statusBar().showMessage('CMEB Connected')

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

        print("egse socket err")

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