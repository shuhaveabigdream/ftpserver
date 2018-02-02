from selectors import DefaultSelector
from selectors import EVENT_READ,EVENT_WRITE
import socket
from multiprocessing import Queue,Process
from threading import Thread
import time
import json
import os,sys

Host='127.0.0.1'
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/Resource/'
socket.setdefaulttimeout(5)

class FtpServer:
    def __init__(self,**kwds):
        self.IpAddr=kwds['ipaddr']
        self.Port=kwds['port']
        self.QueuePorts=kwds['QueuePorts']
        self.QueueInfors=kwds['QueueInfors']
        self.sel=DefaultSelector()
        self.Socket=socket.socket()
    def connect(self):
        self.Socket.bind((self.IpAddr,self.Port))
        self.Socket.listen(100)
        self.Socket.setblocking(False)
        self.sel.register(self.Socket,EVENT_READ,self.accpet)
        while True:
            events=self.sel.select()
            for key,mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    def accpet(self,sock,mask):
        conn,addr=sock.accept()
        conn.setblocking(False)
        self.sel.register(conn,EVENT_READ,self.interface)

    def Task_Upload(self,conn,size,name):
        Error={}
        if not self.QueuePorts.empty():
            tmp = {}
            tmp['port'] = self.QueuePorts.get()
            tmp['action'] = 'Upload'
            tmp['file_size']=size
            tmp['extra']=name
            self.QueueInfors.put(tmp)  # 将信息传入消息队列 本次连接结束
            conn.send(json.dumps({'status': 'True', 'port': tmp['port'],'size':size}).encode('utf-8'))  # 将本次连接结果返回客户端
        else:
            Error['status'] = False
            Error['reason'] = '服务器资源已占满，请稍后再试'
            package = json.dumps(Error)
            conn.send(package.encode('utf-8'))

    def Task_Download(self,conn,path):
        Error = {}
        if os.path.isfile(path)==False:
            Error['status'] = False
            Error['reason'] = '不存在该路径'
            package = json.dumps(Error)
            conn.send(package.encode('utf-8'))
            return
        if not self.QueuePorts.empty():
            tmp = {}
            tmp['port'] = self.QueuePorts.get()
            tmp['action'] = 'Download'
            tmp['extra'] = path
            tmp['file_size']=os.path.getsize(path)
            self.QueueInfors.put(tmp)  # 将信息传入消息队列 本次连接结束
            conn.send(json.dumps({'status': 'True', 'port': tmp['port'],'size':tmp['file_size']}).encode('utf-8'))  # 将本次连接结果返回客户端
        else:
            Error['status'] = False
            Error['reason'] = '服务器资源已占满，请稍后再试'
            package = json.dumps(Error)
            conn.send(package.encode('utf-8'))


    def interface(self,conn,mask):
        Error={}
        date=None
        try:
            date=conn.recv(1024)
        except Exception as e:
         print(e)
        if date:
            package=json.loads(date.decode('utf-8'))
            action=package.get('action',None)
            paths=package.get('path',None)
            if action=='Download':
                self.Task_Download(conn,paths)
            elif action=='Upload':
                filesize=package.get('filesize',None)
                self.Task_Upload(conn,filesize,package['filename'])
            else:
                Error['status'] = False
                Error['reason'] = '错误的指令'
                package = json.dumps(Error)
                conn.send(package.encode('utf-8'))
        else:
            print('lost connect')
            self.sel.unregister(conn)
            conn.close()


class TransServer:#需要修的太多 不继承了
    def __init__(self,**kwd):
        self.IpAddr=kwd['ipaddr']
        self.Port=kwd['port']
        self.action=kwd['action']
        self.extra=kwd['extra']
        self.file_size=kwd['file_size']
        self.extra=kwd['extra']
        self.sel = DefaultSelector()
        self.Socket = socket.socket()
        self.block=True

    def connect(self):
        self.Socket.bind((self.IpAddr,self.Port))
        self.Socket.listen(10)
        self.Socket.setblocking(True)
        self.sel.register(self.Socket,EVENT_READ,self.accpet)
        while self.block:
            events=self.sel.select()
            for key,mask in events:
                callback = key.data
                callback(key.fileobj, mask)
        print('端口关闭')
        self.sel.close()#只进行一次连接

    def accpet(self,sock,mask):
        conn,addr=sock.accept()
        conn.setblocking(True)
        if(self.action=='Download'):
            self.sel.register(conn,EVENT_WRITE,self.Download)
        elif(self.action=='Upload'):
            self.sel.register(conn, EVENT_WRITE, self.Upload)

    def Upload(self,conn,mask):#处理上传问题
        file_size = self.file_size
        file_name = self.extra
        file = open(PATH + file_name, 'wb')  # 打开文件夹
        rest_size = file_size
        conn.send('ACK'.encode('utf-8'))
        while rest_size > 0:
            try:

                part = conn.recv(1024 * 1024)
                if part:
                    file.write(part)
                    rest_size -= len(part)
                    print('rest', rest_size)
                else:
                    raise ValueError('传输错误')
            except Exception as e:
                print(e)
                break
        print('task complete')
        self.block = False
        self.AfterUpload(conn)

    def Download(self,conn,mask):#处理下载问题
        #改进 这里不再需要获取文件相关信息，只需要进行下载
        file = open(self.extra, 'rb')
        file_size=self.file_size
        try:
            date=conn.recv(1024).decode('utf-8')
            if date!='ACK':
                raise ValueError('返回信号不正确')
        except Exception as e:
            print(e)
            self.block=False
            return
        now_size = 0
        for line in file:
            while True:
                try:
                    conn.send(line)
                    now_size += len(line)
                    print('all:%s rest:%s' % (file_size, int(file_size) - now_size))
                    break
                except Exception as e:
                    print(e)
                    self.block = False
                    return
        print('compelet')
        self.block = False
        self.AfterDownload(conn)

    def AfterUpload(self,conn):#上传完成后
        pass

    def AfterDownload(self,conn):#下载完成后
        pass



def Task_Ftp(*args):
    Ports=args[1]
    infor=args[0]
    x=FtpServer(ipaddr=Host,port=8001,QueuePorts=Ports,QueueInfors=infor)
    try:
        x.connect()
    except Exception as e:
        print(e)
        print('连接中断')



def open_server(*args):
    print('open server',args)
    server=TransServer(ipaddr=Host,port=args[1],action=args[2],extra=args[3],file_size=args[4])
    server.connect()
    print('放回端口到队列中')
    args[0].put(args[1])#端口已经用完了 放回去
def Task_Trans(*args):
    Ports=args[1]
    infor=args[0]#path action
    while True:
        if not infor.empty():
            date=infor.get()
            print('Get Task:%s'%date)
            x = Thread(target=open_server,args=[Ports, date['port'], date['action'], date['extra'],date['file_size']])
            x.start()
            time.sleep(0.2)

if __name__=='__main__':
    s=Queue()#文件路径信息
    b=Queue()#可用端口
    for i in range(10):#放入开放的端口
        b.put(i+9000)
    CmdServer=Process(target=Task_Ftp,args=[s,b])
    Trans=Process(target=Task_Trans,args=[s,b])
    CmdServer.start()
    Trans.start()
    CmdServer.join()
