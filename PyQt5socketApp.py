import io
import json
import socket

import struct
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys

class windows(QWidget):
    def __init__(self, parent = None):
        super(windows, self).__init__(parent)
        self.setWindowTitle("QThread 例子")
        self.num = None

        layout = QHBoxLayout()
        layout2 = QVBoxLayout()

        self.label_IP = QLabel("目的IP地址是：")
        self.local_IP = QLabel("本地IP地址是：")
        layout2.addWidget(self.local_IP)
        layout2.addWidget(self.label_IP)

        self.edit = QTextEdit()
        self.edit.setReadOnly(True)

        self.edit2 = QTextEdit(self)
        layout2.addWidget(self.edit)
        layout2.addWidget(self.edit2)

        self.buttonConnect = QPushButton("连接")
        self.buttonSend = QPushButton("发送")
        layout.addWidget(self.buttonConnect)
        layout.addWidget(self.buttonSend)
        layout2.addLayout(layout)

        self.setLayout(layout2)

        self.buttonConnect.clicked.connect(self.showDialog)
        self.buttonSend.clicked.connect(self.sendMsg)


        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clientSend = socketSend()
        self.recv_buffer = None
        self.clientRecv = sockRecv(self.sock)


        ip = socket.getaddrinfo(socket.gethostname(), None)
        ipall=""
        for item in ip:
            if ':' not in item[4][0]:
                ipall += "||"+item[4][0]
        self.local_IP.setText("本地IP地址是："+ipall)

        self.recvThread = recvThread(self.sock)
        self.buttonSend.setEnabled(False)
        self.recvThread.sinOut.connect(self.recvMsgThread)



    def connect2Server(self):
        print("connect to server")

    def showDialog(self):
        dialog = QDialog()
        btn = QPushButton("OK", dialog)
        btn.clicked.connect(self.dialogOK)

        lb1 = QLabel("服务器地址：", dialog)
        lb2 = QLabel("服务器端口：", dialog)
        self.le1 = QLineEdit("127.0.0.1", dialog)
        self.le2 = QLineEdit("8080", dialog)

        layout = QFormLayout(dialog)
        layout.addRow(btn)
        layout.addRow(lb1, self.le1)
        layout.addRow(lb2, self.le2)

        self.listView = QListView(dialog)
        self.stringListModel = QStringListModel()
        self.listView.setModel(self.stringListModel)
        self.listView.clicked.connect(self.selectIP)
        layout.addRow(self.listView)



        dialog.setWindowTitle("Dialog")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

        dialog.setLayout(layout)



    def dialogOK(self):
        print("Dialog OK is clicked")
        addr = self.le1.text()
        port = self.le2.text()
        print("地址：{}，端口：{}".format(addr,port))
        self.sock.connect((addr,int(port)))
        recv_welcom = self.sock.recv(1024)
        recv_welcom = recv_welcom.decode('utf-8')
        print(recv_welcom)
        content = self.clientSend.create_content("search", "***test***")
        content_byte = self.clientSend.json_encode(content, "utf-8")
        message = self.clientSend.create_message("cmd", content_byte, "utf-8")
        self.sock.sendall(message)


        recv = self.sock.recv(1024)
        recv1 = recv.decode('utf-8')
        self.clientRecv.recv_buffer = recv
        print(self.clientRecv.recv_buffer)
        self.clientRecv.get_jsonheader_len()
        self.clientRecv.get_jsonheader()
        self.clientRecv.recv_message()

        content_recv = self.clientRecv.content.decode("utf-8")

        print("recv:{}".format(recv1))
        print("header:{}".format(self.clientRecv.jsonheader))
        print("content:{},type:{}".format(content_recv, type(content_recv)))
        self.list1 = []
        print("list:{}".format(list))

        self.list1 = self.ip_list(content_recv)

        self.stringListModel.setStringList(self.list1)

    def ip_list(self, s):
        ip_pool = []
        s = s.replace("[", "(")
        s = s.replace("]", ")")
        print(s[1:-1])
        s = s[1:-1]

        s = s.split(",")

        print(s)
        for i in s:
            i = i.strip()
            if len(i) != 6:
                #print(i[2:-1])
                #print(len(i))
                ip_pool.append(i[2: -1])
        print("list:{}".format(ip_pool))
        return ip_pool

    def selectIP(self, qModelIndex):
        self.num = qModelIndex.row()
        print("列表中的第{}个".format(self.num))
        index = self.list1[qModelIndex.row()]
        print("选择了：{}".format(index))
        self.label_IP.setText("目的IP地址是："+index)
        self.buttonSend.setEnabled(True)
        self.recvThread.start()


    def sendMsg(self):
        addr = self.num
        content = self.edit2.toPlainText()
        print(content)
        content = self.clientSend.create_content(addr, content)
        content_byte = self.clientSend.json_encode(content, "utf-8")
        message = self.clientSend.create_message("sendString", content_byte, "utf-8")
        self.sock.sendall(message)

    def recvMsgThread(self, msg):
        self.edit.append(msg)

class socketSend():

    def json_encode(self, data, encoding):
        return json.dumps(data, ensure_ascii=False).encode(encoding)

    def json_decode(self, data, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(data), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def create_message(self, content_type, content_byte, content_encoding):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_byte)
        }
        jsonheader_byte = self.json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_byte))
        message = message_hdr + jsonheader_byte + content_byte
        return message

    def create_content(self, action, value, string = None, Img = None):
        if action == "search":
            print("***查询连接列表***")
            content = dict(action="search", value=value)
            return content
        else:
            addr = action
            content = dict(addr=addr, value=value)
            return content

class sockRecv():
    def __init__(self, sock):
        self.sock = sock
        self.recv_buffer = None
        self.send_buffer = None
        self.jsonheader_len = None
        self.jsonheader = None
        self.send_jsonheader = None
        self.send_jsonheader_len = None
        self.content_len = None
        self.content = None

    def json_encode(self, data, encoding):
        return json.dumps(data, ensure_ascii=False).encode(encoding)

    def json_decode(self, data, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(data), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def get_jsonheader_len(self):
        hdrlen = 2
        self.jsonheader_len = struct.unpack(
            ">H", self.recv_buffer[:hdrlen]
        )[0]
        self.recv_buffer = self.recv_buffer[hdrlen:]

    def get_jsonheader(self):
        print("get_jsonheader is running")
        self.jsonheader = self.json_decode(self.recv_buffer[:self.jsonheader_len], "utf-8")
        print("***jsonheader:{}***".format(self.jsonheader))
        self.recv_buffer = self.recv_buffer[self.jsonheader_len:]
        for header in (
            "byteorder",
            "content-type",
            "content-length",
            "content-encoding",
        ):
            if header not in self.jsonheader:
                print("***头文件缺失：{}缺失***".format(header))

    def create_response_message(self, content_byte):
        self.send_jsonheader = {
            "byteorder": sys.byteorder,
            "content-type":self.jsonheader["content-type"],
            "content-encoding":self.jsonheader["content-encoding"],
            "content-length":len(content_byte)
        }
        send_jsonheader_byte = self.json_encode(self.send_jsonheader, self.jsonheader["content-encoding"])
        self.send_jsonheader_len = struct.pack(">H", len(send_jsonheader_byte))
        send_message = self.send_jsonheader_len + send_jsonheader_byte + content_byte
        return send_message

    def recv_message(self):
        self.content_len = self.jsonheader["content-length"]
        current_content_len = len(self.recv_buffer)
        if current_content_len<self.content_len:
            print("***数据较大正在接收***")
            while True:
                data = self.client.recv(1024)
                current_content_len += len(data)
                self.recv_buffer += data
                print("数据接收中（{}/{}".format(current_content_len, self.content_len))
                if current_content_len == self.content_len:
                    print("***数据接收完成***")
                    self.content = self.recv_buffer
                    break
        else:
            self.content = self.recv_buffer

    def process_message(self):
        print("***处理消息***")
        print("消息内容：{}".format(self.content))
        content = self.json_decode(self.content, self.jsonheader["content-encoding"])
        print("消息是：{}".format(content))
        action = content.get("action")
        value = content.get("value")
        print("acton is {}, value is {}".format(action,value))

        if action == "search":
            content_byte = self.json_encode(self.addr_pool,self.jsonheader["content-encoding"])
            send_message = self.create_response_message(content_byte)
            print("***发送消息{}***".format(send_message))
            self.client.sendall(send_message)


    def recv_buff(self):
        self.recv_buffer = self.sock.recv(1024)

    def run(self):
        while True:
            self.recv_buffer = self.client.recv(1024)
            self.get_jsonheader_len()
            self.get_jsonheader()

            self.recv_message()
            self.process_message()

class recvThread(QThread):
    sinOut = pyqtSignal(str)

    def __init__(self, sock, parent= None):
        super(recvThread, self).__init__(parent)
        self.sock = sock
        self.clientRecv = sockRecv(self.sock)

    def run(self):
        print("*-*recvThread is running*-*")
        while True:
            print("-----RECV-------")
            recv = self.sock.recv(1024)
            recv1 = recv.decode('utf-8')
            self.clientRecv.recv_buffer = recv
            print("self.clientRecv.recv_buffer:{}".format(self.clientRecv.recv_buffer))
            self.clientRecv.get_jsonheader_len()
            self.clientRecv.get_jsonheader()
            self.clientRecv.recv_message()
            content_recv = self.clientRecv.content.decode('utf-8')
            print("recv:{}".format(recv1))
            print("header:{}".format(self.clientRecv.jsonheader))
            print("content:{}".format(content_recv))
            self.sinOut.emit(content_recv)
            




if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = windows()
    win.show()
    sys.exit(app.exec_())