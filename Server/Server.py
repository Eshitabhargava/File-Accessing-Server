from uuid import uuid1
from uuid import UUID
from uuid import *
from threading import Thread,Semaphore
import time
import socket
import sys
import os

class Model:
    __model=None
    def __new__(cls):
        if Model.__model==None:
            Model.__model=super().__new__(cls)
        return Model.__model    
    def __init__(self):
        self.users_credentials=dict()
        self.users=dict()
        self.file_store=dict() 

class Processor(Thread):
    def __init__(self,sock,model):
        Thread.__init__(self)
        self.sock=sock
        self.model=model
        self.start()
    def run(self):
#receiving user_config str len
        data_bytes=b''
        to_receive=1024
        while len(data_bytes)<to_receive:
            by=self.sock.recv(to_receive-len(data_bytes))
            data_bytes+=by
        user_config_str_len=int(data_bytes.decode("utf-8").strip())
#receiving user_config str
        data_bytes=b''
        to_receive=user_config_str_len
        while len(data_bytes)<to_receive:
            by=self.sock.recv(to_receive-len(data_bytes))
            data_bytes+=by
        user_config=eval(data_bytes.decode("utf-8"))
        username=str(user_config[0])
        password=user_config[1]
        if not username in self.model.users_credentials: response="(\"Invalid username\",)"
        else:
            if self.model.users_credentials[username]!=password: response="(\"Invalid password\",)"
            else:
                 user_uid=str(uuid1())
                 self.model.users[user_uid]=user_config
                 response=("Valid",user_uid)
        response_string=str(response)
        #sending len credentials response
        self.sock.sendall(bytes(str(len(response_string)).ljust(1024),"utf-8"))
        #sending credentials response
        self.sock.sendall(bytes(response_string,"utf-8"))
        while True:
            #receiving request string length
            data_bytes=b''
            to_receive=1024
            while len(data_bytes)<to_receive:
                by=self.sock.recv(to_receive-len(data_bytes))
                data_bytes+=by
            request_length=int(data_bytes.decode("utf-8").strip())
            #receiving request string
            data_bytes=b''
            to_receive=request_length
            while len(data_bytes)<to_receive:
               by=self.sock.recv(to_receive-len(data_bytes))
               data_bytes+=by
            request_string=eval(data_bytes.decode("utf-8").strip())
            uid=request_string[0]
            if not uid in self.model.users: 
                ack="_$invalid$_"
                #sending ack len
                self.sock.sendall(bytes(str(len(ack)).ljust(1024),"utf-8"))
                #sending ack
                self.sock.sendall(bytes(ack,"utf-8"))
                break
            ack="_$valid$_"
            #sending ack len
            self.sock.sendall(bytes(str(len(ack)).ljust(1024),"utf-8"))
            #sending ack
            self.sock.sendall(bytes(ack,"utf-8"))
            request=request_string[1].lower()
            if request=="dir":
                response=""
                for file_name,file_size in self.model.file_store.items():
                    response+=file_name.rjust(30,' ')
                    response+=' '*5
                    response+=str(file_size).ljust(10,' ')
                    response+='\n'
                #sending size of response
                size=len(response)
                self.sock.sendall(bytes(str(size).ljust(1024),"utf-8"))
                #sending response
                response_bytes=bytes(response,"utf-8")
                bytes_sent=0
                chunk_size=4096
                start_index=0
                #uploading file
                while bytes_sent<size:
                    if(chunk_size>(size-bytes_sent)): chunk_size=size-bytes_sent
                    to_send=response_bytes[start_index:chunk_size]
                    start_index+=chunk_size
                    bytes_sent+=chunk_size
                    self.sock.sendall(to_send)
            if request[0:8]=="download":
                to_upload=request_string[2]
                if not to_upload in self.model.file_store: 
                    ack="_$invalid$_"
                    #sending ack len
                    self.sock.sendall(bytes(str(len(ack)).ljust(1024),"utf-8"))
                    #sending ack
                    self.sock.sendall(bytes(ack,"utf-8"))
                else: 
                    ack="_$valid$_"
                    #sending ack len
                    self.sock.sendall(bytes(str(len(ack)).ljust(1024),"utf-8"))
                    #sending ack
                    self.sock.sendall(bytes(ack,"utf-8"))
                    sem_obj=self.model.file_store[to_upload][1]
                    sem_obj.acquire()
                    #determining size of file to be uploaded
                    size=self.model.file_store[to_upload][0]
                    #sending size of file to be uploaded
                    self.sock.sendall(bytes(str(size).ljust(1024),"utf-8"))
                    print("Sending size of file to be uploaded.... ")
                    file=open("Store\\"+to_upload,"rb")
                    bytes_sent=0
                    chunk_size=4096
                    #uploading file
                    while bytes_sent<size:
                        if(chunk_size>(size-bytes_sent)): chunk_size=size-bytes_sent
                        to_send=file.read(chunk_size)
                        self.sock.sendall(to_send)
                        bytes_sent+=chunk_size
                        time.sleep(0.25)
                    print(to_upload," sent!")
                    file.close()
                    sem_obj.release()
            if request=="exit": 
                del self.model.users[uid]
                break

                
serverSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
serverSocket.bind(("localhost",5500))
serverSocket.listen()
model=Model()
users_config_file=open("users.cfg","r")
while True:
    line=users_config_file.readline()
    if len(line)==0: break
    user_data=eval(line)
    model.users_credentials[user_data[0]]=user_data[1]
files=os.listdir("Store")
file_size=[]
for file in files:
    model.file_store[str(file.lower())]=(os.stat("Store\\"+file).st_size,Semaphore(2))

while True:
    print("Server is in listening mode")
    sock,sock_name=serverSocket.accept()
    pr=Processor(sock,model)
