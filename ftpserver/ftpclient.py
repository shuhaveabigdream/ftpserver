from socket import socket
import json
import os,sys
import time

SAVEPATH='H://Resource/'


class MyClient:
    def __init__(self,**kwds):
        self._Cmd=socket()
        self._Trans=socket()
        print('Client system init!')
    def _Connect(self,**kwds):
        try:
            self._Cmd.connect((kwds['Ipaddr'],int(kwds['Port'])))
            self.ipaddr=kwds['Ipaddr']
            return True
        except Exception as e:
            print(e)
            return False

    def _CheckPath(self,Path):
        if os.path.isfile(Path):
            return True
        else:
            return False
    def _Cmd_Upload(self,Path):
        date={}
        date['action'] = 'Upload'
        date['path'] = 'f://爱下电影.txt'
        date=json.dumps(date)#打包成JSON
        self._Cmd.send(date.encode('utf-8'))
        callback=self._Cmd.recv(1024)#接受反馈数据
        callback=json.loads(callback.decode('utf-8'))
        if callback['status']:
            print('服务器响应正确')
            time.sleep(0.5)
            try:
                self._Trans.connect((self.ipaddr,callback['port']))
            except:
                print('链接错误')
                return False
            self._Trans.send('Ready'.encode('utf-8'))
            callback=self._Trans.recv(1024)
            if callback.decode('utf-8')!='ACK':
                print('服务器响应不正确 time0')
                self._Trans.close()
                return False
            file_size=os.path.getsize(Path)
            date={}
            date['filename']='test.txt'
            date['filesize']=file_size
            date=json.dumps(date)
            self._Trans.send(date.encode('utf-8'))
            callback= self._Trans.recv(1024)
            if callback.decode('utf-8')!='ACK':
                print('服务器响应不正确 time1')
                self._Trans.close()
                return False
            file=open(Path,'rb')
            for i in file:
                while True:
                    try:
                        self._Trans.send(i)
                        file_size -= len(i)
                        print('剩余:%s' % file_size)
                        break
                    except Exception as e:
                        print(e)
                        time.sleep(0.1)
            self._Trans.close()
            print('本次传输完成!')
        else:
            print('Error!')
            print('Reason',callback['reason'])
            return  False
    def _Cmd_Download(self,Path):
        date={}
        date['action']='Download'
        date['path']=Path
        package=json.dumps(date)
        package=package.encode('utf-8')
        self._Cmd.send(package)
        callback=self._Cmd.recv(1024)
        callback=callback.decode('utf-8')
        callback=json.loads(callback)
        if callback['status']=='True':
            try:
                self._Trans.connect((self.ipaddr,callback['port']))
            except:
                print('链接失败')
                return
            file=open(SAVEPATH+'test.sm','wb')
            time.sleep(0.5)
            self._Trans.send('Ready'.encode('utf-8'))
            callback=self._Trans.recv(1024)
            callback=json.loads(callback.decode('utf-8'))
            file_size=callback['filesize']
            while file_size > 0:
                date = self._Trans.recv(1024 * 1024)
                file.write(date)
                file_size-= len(date)
                print('剩余%s未下载,本次包长度:%s' % (file_size, len(date)))
            print('本次下载完成')
            file.close()
        else:
            print('ERROR')
            print(callback)
            print('reason',callback['reason'])
            return
    def Shell(self):
        while True:
            Ipaddr=input('输入服务器所在ip地址:')
            Port=input('输入服务器端口:')
            print('尝试连接......')
            if self._Connect(Ipaddr=Ipaddr,Port=Port):
                break
        print('连接成功')

        while True:
            Ord=input('1.上传文件\n2.下载文件\n3.退出\n')
            if Ord=='1':
                Path=input('输入本地文件地址(绝对路径):')
                if self._CheckPath(Path):
                    self._Cmd_Upload(Path)
                else:
                    print('该路径不存在，请检查')
            elif Ord=='2':
                Path=input('输入需要下载的文件地址(绝对路径):')
                self._Cmd_Download(Path)
            elif Ord=='3':
                return
            else:
                print('无效指令')



if __name__=='__main__':
    if os.path.exists(SAVEPATH)==False:
        print('指定的下载存放路径不正确')
    x=MyClient()
    x.Shell()
    print('Bye!')
    sys.exit(0)