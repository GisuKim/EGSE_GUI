from numbers import Number
from PyQt5.QtWidgets import *
from PyQt5 import uic

openWidget = uic.loadUiType("OpenSettingWidget.ui")[0]

class OpenSetting(QWidget, openWidget):

    cmebIP = "192.168.10.10"
    cmebPort = 7000
    egseIP = "192.168.10.26"
    egsePort = 8000

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tb_cmeb_ip_a.setText(self.cmebIP.split('.')[0])
        self.tb_cmeb_ip_b.setText(self.cmebIP.split('.')[1])
        self.tb_cmeb_ip_c.setText(self.cmebIP.split('.')[2])
        self.tb_cmeb_ip_d.setText(self.cmebIP.split('.')[3])
        self.tb_cmeb_port.setText(str(self.cmebPort))
        self.tb_egse_ip_a.setText(self.egseIP.split('.')[0])
        self.tb_egse_ip_b.setText(self.egseIP.split('.')[1])
        self.tb_egse_ip_c.setText(self.egseIP.split('.')[2])
        self.tb_egse_ip_d.setText(self.egseIP.split('.')[3])
        self.tb_egse_port.setText(str(self.egsePort))


    def GetIP(self):

        cmeb_ip = ""
        egse_ip = ""
        cmeb_port = 0
        egse_port = 0

        a = list()

        a.append(self.tb_cmeb_ip_a.toPlainText())
        a.append(self.tb_cmeb_ip_b.toPlainText())
        a.append(self.tb_cmeb_ip_c.toPlainText())
        a.append(self.tb_cmeb_ip_d.toPlainText())
        a.append(self.tb_egse_ip_a.toPlainText())
        a.append(self.tb_egse_ip_b.toPlainText())
        a.append(self.tb_egse_ip_c.toPlainText())
        a.append(self.tb_egse_ip_d.toPlainText())
        a.append(self.tb_cmeb_port.toPlainText())
        a.append(self.tb_egse_port.toPlainText())

        for idx, i in enumerate(a):
            if idx < 7:
                if idx < 4:
                    if idx == 3:
                        cmeb_ip += i
                    else:
                        cmeb_ip += i + '.'
                else:
                    egse_ip += i + '.'
            else:
                if idx < 8:
                    egse_ip += i
                else:
                    if idx < 9:
                        cmeb_port = int(i)
                    else:
                        egse_port = int(i)


        print(" CMEB IP : " + cmeb_ip + "\n", "EGSE IP : " + egse_ip + "\n")

        return (cmeb_ip, cmeb_port, egse_ip, egse_port)


