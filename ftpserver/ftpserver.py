from selectors import DefaultSelector
from selectors import EVENT_READ,EVENT_WRITE
import socket
from multiprocessing import Queue,Process
from threading import Thread
import time
import json
import os,sys

Host='127.0.0.1'
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'Resource/'
SAVEPATH='f://Resource/'

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
    def interface(self,conn,mask):
        Error={}
        try:
            date=conn.recv(1024)
            if date:
                package=json.loads(date.decode('utf-8'))
                action=package.get('action',None)
                paths=package.get('path',None)
                if action=='Download' or action=='Upload':
                    if os.path.isfile(paths):
                        if not self.QueuePorts.empty():
                            tmp={}
                            tmp['port'] =self.QueuePorts.get()
                            tmp['action']=action
                            tmp['path']=paths
                            self.QueueInfors.put(tmp)#将信息传入消息队列 本次连接结束
                            conn.send(json.dumps({'status':'True','port':tmp['port']}).encode('utf-8'))#将本次连接结果返回客户端
                        else:
                            Error['status'] = False
                            Error['reason'] = '服务器资源已占满，请稍后再试'
                            package = json.dumps(Error)
                            conn.send(package.encode('utf-8'))
                    else:
                        Error['status'] = False
                        Error['reason'] = '不存在该路径'
                        package = json.dumps(Error)
                        conn.send(package.encode('utf-8'))
                else:
                    Error['status']=False
                    Error['reason']='错误的指令'
                    package=json.dumps(Error)
                    conn.send(package.encode('utf-8'))
            else:
                print('lost connect')
                self.sel.unregister(conn)
                conn.close()
        except Exception as e:
            print(e)

class TransServer:#需要修的太多 不继承了
    def __init__(self,**kwd):
        self.IpAddr=kwd['ipaddr']
        self.Port=kwd['port']
        self.path=kwd['path']
        self.action=kwd['action']
        self.sel = DefaultSelector()
        self.Socket = socket.socket()
        self.block=True

    def connect(self):
        self.Socket.bind((self.IpAddr,self.Port))
        self.Socket.listen(10)
        self.Socket.setblocking(False)
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
        conn.setblocking(False)
        self.sel.register(conn,EVENT_READ,self.interface)

    def interface(self,conn,mask):
        conn.setblocking(True)
        try:
            date=conn.recv(1024)
            date=date.decode('utf-8')
            print('date',date)
        except Exception as e:
            print(e)
            self.sel.unregister(conn)
            conn.close()
            return
        if date=='Ready':
            if self.action=='Download':
                ans={}
                ans['statue']=True
                file=open(self.path,'rb')
                file_size=os.path.getsize(self.path)
                print('file_size',file_size)
                ans['filesize'] =file_size
                conn.send(json.dumps(ans).encode('utf-8'))
                now_size=0
                for line in file:
                    while True:
                        try:
                            conn.send(line)
                            now_size+=len(line)
                            print('all:%s rest:%s'%(file_size,int(file_size)-now_size))
                            break
                        except Exception as e:
                            print(e)
                            time.sleep(0.1)
                print('compelet')
                self.block=False
            elif self.action=='Upload':#上传步骤
                conn.send('ACK'.encode('utf-8'))#发送一个ACK信号让客户端开始上传
                tmp=conn.recv(1024)
                time.sleep(0.1)
                try:
                    tmp=json.loads(tmp.decode('utf-8'))
                    print('tmp',tmp)
                except:
                    print('编码错误',tmp)
                    self.block=False
                    return
                conn.send('ACK'.encode('utf-8'))
                file_size=tmp['filesize']#获取文件大小
                file_name=tmp['filename']
                file=open(SAVEPATH+file_name,'wb')#打开文件夹
                rest_size=file_size
                while rest_size>0:
                    part=conn.recv(1024*1024)
                    file.write(part)
                    rest_size-=len(part)
                    print('rest',rest_size)
                print('complete')
                self.block=False
        else:
            print('lost connect')
            conn.close()

def Task_Ftp(*args):
    Ports=args[1]
    infor=args[0]
    x=FtpServer(ipaddr=Host,port=8001,QueuePorts=Ports,QueueInfors=infor)
    x.connect()


def open_server(*args):
    print('open server',args)
    server=TransServer(ipaddr=Host,port=args[1],path=args[2],action=args[3])
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
            x=Thread(target=open_server,args=[Ports,date['port'] ,date['path'],date['action']])
            x.start()
            time.sleep(0.2)

if __name__=='__main__':
    s=Queue()#文件路径信息
    b=Queue()#可用端口
    s.empty()
    for i in range(10):#放入开放的端口
        b.put(i+9000)
    CmdServer=Process(target=Task_Ftp,args=[s,b])
    Trans=Process(target=Task_Trans,args=[s,b])
    CmdServer.start()
    Trans.start()
    CmdServer.join()
