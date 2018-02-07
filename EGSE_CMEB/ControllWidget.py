from PyQt5.QtWidgets import *
from PyQt5 import QtCore, uic, QtGui
import cv2
import numpy
import numpy as np
import queue
import threading
import tcp_Client
import sys
import time
import main

running = False
capture_thread = None
ControlWidget = uic.loadUiType("ControllUI.ui")[0]
q = queue.Queue()
sendq = queue.Queue()

FRAME_WIDTH = 2048
FRAME_HEIGHT = 2048
CHANNEL = 2       #16BIT BGR565
IMAGE_SIZE = FRAME_WIDTH * FRAME_HEIGHT * CHANNEL

TCP_TxLOOP = 32
TCP_TxLen = (FRAME_WIDTH*FRAME_HEIGHT*CHANNEL)/TCP_TxLOOP

ICON_RED_LED = "icon/led-red-on.png"
ICON_GREEN_LED = "icon/green-led-on.png"

## Mode Define
MODE_MESSAGE_READ = 0
MODE_CBIT_READ = 1
MODE_IMAGE_READ = 2


def grab(cam, queue, sendqueue, width, height, fps):
    global running
    capture = cv2.VideoCapture(cam)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)
    print("camera Ready")
    while(running):
        frame = {}
        capture.grab()
        retval, img = capture.retrieve(0)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGR565)      #컬러포맷 변경 3->2 byte
        frame["img"] = img

        print(img.shape)

        if queue.qsize() < 10:
            queue.put(frame)
        else:
            print(queue.qsize())

        if sendqueue.qsize() < 10:
            sendqueue.put(frame)
        else:
            print(sendqueue.qsize())

class OwnImageWidget(QWidget):
    def __init__(self, parent=None):
        super(OwnImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)

        qp.end()


## ContrilDisplay class.
#
# 이미지를 변환 하여 PyQT의 Widget에 표시한다.
class ControlDisplay(QWidget, ControlWidget, tcp_Client.TCPClient):

    ## Class Variable
    readMode = MODE_MESSAGE_READ
    isConnect = False
    isSSR = False
    imageFname = ''
    img = ()
    frame={}
    myWindow = QMainWindow
    imageReadCNT = 0
    receiveImage = b''
    cmebinst = None


    ## Constructor
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        tcp_Client.TCPClient.__init__(self)

        # self.btn_send_image.setEnabled(False)
        # self.btn_read_image.setEnabled(False)


        self.btn_get_fpa.clicked.connect(self.GetFPAStatus)
        self.btn_TrigerCameraButton.clicked.connect(self.TriggerCameraClicked)     #TriggerCamera Button
        self.btn_GetResultImage.clicked.connect(self.GetResultImageClicked)          #Request Result image Buttton
        self.btn_send_image.clicked.connect(self.ImageSendButtonClicked)    #d이미지 전송 시작
        self.btn_read_image.clicked.connect(self.ImageReadButtonClicked)    #이미지 수신 시작
        self.btn_CMEB_Power.clicked.connect(self.CMEBPowerOnClicked)        #CMEB Power Switch
        self.btn_camera_on.clicked.connect(self.start_clicked)

        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()
        self.ImgWidget = OwnImageWidget(self.ImgWidget)
        self.ImgReturn = OwnImageWidget(self.ImgReturn)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)


        # self.btn_get_fpa.clicked.connect()

    def TriggerCameraClicked(self):
        # self.write_buffer = "REQ_CAM_START"
        # sent = self.send(self.write_buffer.encode())
        # self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        # self.write_buffer = self.write_buffer[sent:]

        self.cmebinst.write_buffer = "RE_RX_IMAGE"
        sent = self.cmebinst.send(self.cmebinst.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.cmebinst.write_buffer[:sent])
        self.cmebinst.write_buffer = self.cmebinst.write_buffer[sent:]

    def GetResultImageClicked(self):
        # self.write_buffer = "GET_RESULT_IMAGE"
        self.write_buffer = "ENABLE_SERDES"
        sent = self.send(self.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]

    def GetFPAStatus(self):
        self.write_buffer = "REQ_CAM_START"
        sent = self.send(self.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]

    def CMEBPowerOnClicked(self):
        if not self.isSSR:
            self.write_buffer = "SSR_ON"
        else:
            self.write_buffer = "SSR_OFF"
        sent = self.send(self.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]

    ## 정보표시창 에 이벤트 발생 시간 및 이벤트를 표시 한다.
    #  @param self The object pointer.
    #  @param _message 정보표시 창에 입력할 문자열
    def SetConsoleMessage(self, _message):
        self.pte_console.appendPlainText(QtCore.QTime.currentTime().toString() + ' : ' + _message)

    ## 이미지 파일 open 시 경로를 저장한다.
    #  @param self The object pointer.
    #  @param _message 정보표시 창에 입력할 문자열
    def SetSendImageFileName(self, _fname):
        self.imageFname = _fname

    def GetImageData(self):
        if not sendq.empty():
            print("Get Queue")
            frame = sendq.get()
            data = numpy.array(frame)  # conversion numpy array
            stringData = data.tostring()  # conversion numpy to string
            return stringData

    ## 불러온 이미지 파일을 전송 하기 위하여 메세지를 전송한다.
    #  @param self The object pointer.
    def ImageSendButtonClicked(self):
        self.timer.stop()
        if not q.empty():
            # self.btn_msg_01.setText('Camera is live')
            frame = q.get()
            self.ImgWidget.setImage(self.image_Transfrom(frame))
            self.img = frame["img"]
        self.write_buffer = "RX_IMAGE"
        sent = self.send(self.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]

    def ImageReadButtonClicked(self):
        self.write_buffer = "RE_RX_IMAGE"
        sent = self.send(self.write_buffer.encode())
        self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]


    def ShowOpenImage(self):
        self.img = cv2.imread(self.imageFname[0], 1)                 #파일오픈
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGR565)      #컬러포맷 변경 3byte->2byte
        # cv2.imshow('1', cv2.cvtColor(self.img, cv2.COLOR_BGR5652BGR))
        img_height, img_width, img_colors = self.img.shape           #이미지의 크기 및 컬러 포맷을 가져옴
        scale_w = float(FRAME_WIDTH) / float(img_width)              #목표 크기와 읽은 파일의 배율을 얻는다.
        scale_h = float(FRAME_HEIGHT) / float(img_height)
        self.img = cv2.resize(self.img, None, fx=scale_w, fy=scale_h, interpolation=cv2.INTER_AREA)    #전송할 이미지의 크기를 변경한다.
        # cv2.imshow('2', cv2.cvtColor(self.img, cv2.COLOR_BGR5652BGR))
        print(self.img.shape)
        self.frame["img"] = self.img
        self.ImgWidget.setImage(self.image_Transfrom(self.frame))   #이미지 표시 위젯에 불러들인 이미지를 표시한다.
        self.SetConsoleMessage(self.imageFname[0] + " is Opened")   #파일이 정상적으로 오픈되었음을 콘솔에 표시
        self.btn_send_image.setEnabled(True);                       #전송버튼을 활성화 한다.

    ## 이미지를 불러와 전송 한다.
    #  @param self The object pointer.
    def ImageSendStart(self):
        img_height, img_width, img_colors = self.img.shape           #이미지의 크기 및 컬러 포맷을 가져옴
        scale_w = float(FRAME_WIDTH) / float(img_width)              #위젯의 윈도우 크기 대비 이미지의 스케일을 계산한다.
        scale_h = float(FRAME_HEIGHT) / float(img_height)
        self.img = cv2.resize(self.img, None, fx=scale_w, fy=scale_h, interpolation=cv2.INTER_CUBIC)
        self.logger.debug(self.img.shape)

        if len(self.img) > 0:
            data = numpy.array(self.img)                        # conversion numpy array
            # data1D = data.reshape(TCP_TxLOOP, (TCP_TxLen))
            # # tx image loop
            # for i in range(0, TCP_TxLOOP):
            #     stringData = data1D[i, :].tostring()  # (2048x2048x2)/ 32 conversion numpy to string
            #     print(' send image array ..  ')
            #     client_socket.send(stringData);
            #     self.write_buffer =
            self.write_buffer = data.tostring()                 # conversion numpy to string
            try:
                self.SetConsoleMessage(str(sys.getsizeof(self.write_buffer)))
                sent = self.send(self.write_buffer)
                self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
                self.write_buffer = self.write_buffer[sent:]
                self.btn_send_image.setEnabled(False);
                self.btn_read_image.setEnabled(True);
            except:
                pass
        else:
            self.SetConsoleMessage('Not Select File')


    def ImageSend(self):
        self.write_buffer = self.MyControll.GetImageData()
        # self.EGSESocket.send()

    def MessageSend1(self):
        print("send Click")
        msg = 'testtest'
        self.send(msg.encode())

    def start_clicked(self):
        global running
        running = True
        capture_thread.start()
        self.btn_camera_on.setEnabled(False)
        self.btn_camera_on.setText('Starting...')

    def image_Transfrom(self, image):
        img = image["img"]
        img_height, img_width, img_colors = img.shape               #이미지의 크기 및 컬러 포맷을 가져옴
        scale_w = float(self.window_width) / float(img_width)       #표시할 파일 크기로 배율을 계산한다.
        scale_h = float(self.window_height) / float(img_height)
        scale = min([scale_w, scale_h])
        # cv2.imshow('tst', cv2.cvtColor(img, cv2.COLOR_BGR5652BGR))
        img = cv2.cvtColor(img, cv2.COLOR_BGR5652BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)      #표시할 이미지 크기를 조정한다.
        height, width, bpc = img.shape
        bpl = bpc * width
        self.logger.debug('Image Forrmat show')
        self.logger.debug(width)
        self.logger.debug(height)
        self.logger.debug(bpl)
        return QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)

    def update_frame(self):

        if not q.empty():
            # self.btn_msg_01.setText('Camera is live')
            frame = q.get()
            # img = frame["img"]
            #
            # img_height, img_width, img_colors = img.shape
            # scale_w = float(self.window_width) / float(img_width)
            # scale_h = float(self.window_height) / float(img_height)
            # scale = min([scale_w, scale_h])
            #
            # if scale == 0:
            #     scale = 1
            # # shrink = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            # img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            # # bgr565 = cv2.cvtColor(shrink, cv2.COLOR_BGR2BGR565)
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # # img = cv2.cvtColor(img, cv2.COLOR_BGR2BGR565)
            # height, width, bpc = img.shape
            # bpl = bpc * width
            # image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            self.ImgWidget.setImage(self.image_Transfrom(frame))

    def closeEvent(self, event):
        global running
        running = False

    def handle_connect(self):
        print("egse connected")
        self.isConnect = True       #Socket이 Serverdp Access 되었음을 알린다.
        self.SetConsoleMessage(str(self.address) + ' ' + 'New Connection')
        # self.logger.debug('handle_connect()')
        # self.readMode = MODE_CBIT_READ
        # self.thTimer = threading.Timer(1, self.SendGetCmebStatusMessage)
        # self.thTimer.start()

    def handle_close(self):
        self.isConnect = False       #Socket이 Close 되었음을 알린다.
        self.SetConsoleMessage(str(self.address) + ' ' + 'Socket Closed')
        self.logger.debug('handle_close()')
        self.thTimer.cancel()
        self.close()
        self.sockThread.join()

    # def writable(self):
    #     is_writable = (len(self.write_buffer) > 0)
    #     if is_writable:
    #         pass
    #         self.logger.debug('writable() -> %s', is_writable)
    #     return is_writable

    # def readable(self):
    #     self.logger.debug('readable() -> True')
    #     return True

    # def handle_write(self):
    #     sent = self.send(self.write_buffer)
    #     self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
    #     self.write_buffer = self.write_buffer[sent:]

    def SendGetCmebStatusMessage(self):
        self.readMode = MODE_CBIT_READ
        self.write_buffer = "GET_CMEB_STATUS_MESSAGE"
        sent = self.send(self.write_buffer.encode())
        # self.logger.debug('handle_write() -> "%s"', self.write_buffer[:sent])
        self.write_buffer = self.write_buffer[sent:]
        self.thTimer = threading.Timer(0.02, self.SendGetCmebStatusMessage)
        self.thTimer.start()

    def SetCmebStatusUI(self, data):
        if data[0] == 1:
            self.lb_led_cbit_power.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
        else:
            self.lb_led_cbit_power.setPixmap(QtGui.QPixmap(ICON_RED_LED))

        self.lb_ver.setText(str(data[14]))
        self.lb_hbeat.setText(str(data[15]))

    def socketToNumpy(self, cameraFeed, sockData):
        k = 2
        j = cameraFeed.shape[1]
        i = cameraFeed.shape[0]
        sockData = np.fromstring(sockData, np.uint8)
        cameraFeed = np.tile(sockData, 1).reshape((i, j, k))

        return cameraFeed

    def DataToImage(self, data):
        shape = (FRAME_HEIGHT, FRAME_WIDTH, CHANNEL)
        cameraFeed = np.zeros(shape, np.uint8)
        print(len(data))
        cameraFeed = self.socketToNumpy(cameraFeed, data)
        # cameraFeed = cv2.cvtColor(cameraFeed, cv2.COLOR_BGR5652BGR)  # 컬러포맷 변경
        # cameraFeed = cv2.cvtColor(cameraFeed, cv2.COLOR_BGR2RGB)
        return  cameraFeed

    def Test(self):
        print('이것은 테스트임')

    def handle_read(self):
        data = self.recv(8192)
        self.logger.debug('handle_read() -> %d bytes', len(data))
        self.logger.debug('mode : %d', self.readMode)
        if self.readMode == MODE_MESSAGE_READ:
            if data.decode()=="RX_IMAGE":      #Image 전송요청 회신시
                self.ImageSendStart()             #Image 전송!
            elif data.decode()=="RE_RX_IMAGE":
                self.imageReadCNT = 0
                print('클리 됐냐 ? %d', self.imageReadCNT)
                self.readMode = MODE_IMAGE_READ
            elif data.decode()=="SSR_ON":
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
                    if(self.imageReadCNT == IMAGE_SIZE):

                        img = self.DataToImage(self.receiveImage)
                        self.receiveImage = b''
                        self.readMode = MODE_MESSAGE_READ
                        self.imageReadCNT = 0

                        img = cv2.resize(img, None, fx=1, fy=1, interpolation=cv2.INTER_CUBIC)
                        # height, width, bpc = img.shape
                        # print(img.shape)
                        # bpl = bpc * width
                        frame  ={}
                        frame["img"] = img
                        self.ImgReturn.setImage(self.image_Transfrom(self.frame))
                        # print('display check ')
                        # cv2.imshow('from image echo SERVER', cv2.cvtColor(img, cv2.COLOR_BGR5652BGR))
                        # cv2.waitKey(0)
                        # cv2.destroyAllWindows()

        # self.read_buffer.write(data)

capture_thread = threading.Thread(target=grab, args = (0, q, sendq, 320, 240, 1))