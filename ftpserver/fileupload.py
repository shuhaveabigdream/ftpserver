from socket import socket
import json
import sys
import os
import time
HOST='127.0.0.1'
PORT=8001
PATH='f://爱下电影.txt'
if __name__=='__main__':
    if os.path.isfile(PATH)==False:
        print('路径不存在')
        sys.exit(0)
    x=socket()
    x.connect((HOST,PORT))
    print('连接成功')
    date={}
    date['action']='Upload'
    date['path']='f://爱下电影.txt'
    date=json.dumps(date)
    print('发送上传指令')
    x.send(date.encode('utf-8'))
    callback=x.recv(1024)
    x.close()
    callback=json.loads(callback.decode('utf-8'))
    trans_port=callback['port']
    print(callback)
    y=socket()
    y.connect((HOST,trans_port))
    y.send('Ready'.encode('utf-8'))
    callback=y.recv(1024)
    if callback.decode('utf-8')!='ACK':
        print('传输错误')
        y.close()
        sys.exit(0)
    file_size=os.path.getsize(PATH)
    date={}
    date['filename']='test.txt'
    date['filesize']=file_size
    date=json.dumps(date)
    date=date.encode('utf-8')
    y.send(date)
    date=y.recv(1024)
    if date.decode('utf-8')!='ACK':
        print('响应错误')
        y.close()
        sys.exit(0)
    file=open(PATH,'rb')
    for i in file:
        while True:
            try:
                y.send(i)
                file_size-=len(i)
                print('rest:%s'%file_size)
                break
            except Exception as e:
                print(e)
                time.sleep(0.1)
    print('complete!')
    print('port',trans_port)
    sys.exit(0)



