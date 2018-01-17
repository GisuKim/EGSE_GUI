import sys

import tcp_Client
import ControllWidget
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore
import OpenSetting
import logging
import time
import cv2

mainWindowWidget = uic.loadUiType("windowMain.ui")[0]

class MainWindow(QMainWindow, mainWindowWidget):

    img = ()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        logging.basicConfig(level=logging.DEBUG,
                            format='%(name)s: %(message)s',
                            )
        self.isConnect = False
        self.setWindowTitle("CMEB EGSE")
        self.actionOpenImage.triggered.connect(self.OpenImageFile)
        self.MyControll = ControllWidget.ControlDisplay()
        self.NewSetting = OpenSetting.OpenSetting()
        self.NewSetting.ConnectButton.clicked.connect(self.btnConnectClicked)  # 설정 완료 버튼 Connect
        self.NewSetting.CancelButton.clicked.connect(self.btnCancelClicked)  # 설정 취소 보튼 Connect
        self.NewSetting.show()
        self.showMinimized()



    def OpenImageFile(self):
        print("open clicked")
        dlg = QFileDialog(self)
        fname = dlg.getOpenFileName(self)
        self.MyControll.SetSendImageFileName(fname) #파일이름 가져오기
        if fname:
            print("pass")
            self.MyControll.ShowOpenImage()

    def SocketRead(self):
        pass

    def btnConnectClicked(self):
        print("connect clicked")
        adress = self.NewSetting.GetIP()
        self.MyControll.connectSocket(adress[2], adress[3])
        time.sleep(1)
        if self.MyControll.isConnect:
            self.NewSetting.close()
            self.showNormal()
            self.setCentralWidget(self.MyControll)

    def btnCancelClicked(self):
        print("cancel clicked")
        self.showNormal()
        self.NewSetting.close()