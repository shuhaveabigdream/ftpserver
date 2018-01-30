from socket import socket
import time
import json
filepath='C://Users/Administrator/Downloads/C8051F120单片机中文数据手册.pdf'
savepath='F://Resource/'

if __name__=='__main__':
    x=socket()
    x.connect(('127.0.0.1',8001))
    date_to_send={}
    date_to_send['action']='Download'
    date_to_send['path']=filepath
    package=json.dumps(date_to_send)
    x.send(package.encode('utf-8'))
    date=x.recv(1024)
    date=json.loads(date.decode('utf-8'))
    print('callback',date)
    print('sleep 1s')
    time.sleep(1)
    file=open(savepath+'8sqKS6y6.mp4','wb')
    y=socket()
    y.connect(('127.0.0.1',date['port']))
    y.send('Ready'.encode('utf-8'))
    tmp=y.recv(1024)
    tmp.decode('utf-8')
    tmp=json.loads(tmp)
    print('callback',tmp)
    size=tmp['filesize']
    while size>0:
        date = y.recv(1024 * 1024)
        file.write(date)
        size-=len(date)
        print ('剩余%s未下载,本次包长度:%s'%(size,len(date)))
    file.close()
    time.sleep(5)
