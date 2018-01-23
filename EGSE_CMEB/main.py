import sys
from PyQt5.QtWidgets import QApplication

import OpenSetting
import MainWindow
import logging

class connetInfo(object):
    cmebIP = "192.168.10.10"
    cmebPort = 7000
    egseIP = "192.168.10.201"
    egsePort = 70

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)s: %(message)s',
                        )
    app = QApplication(sys.argv)
    conInfo = connetInfo()
    myWindow = MainWindow.MainWindow()
    FirstSetting = OpenSetting.OpenSetting()
    myWindow.show()
    app.exec_()