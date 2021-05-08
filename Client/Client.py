from uuid import UUID
import socket
import sys
import os
import math

def is_valid(socket):
        #receiving len of ack to determine if user_uid is valid
        data_bytes=b''
        to_receive=1024
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        ack_length=int(data_bytes.decode("utf-8").strip())
        #receiving ack to determine if user_uid is valid
        data_bytes=b''
        to_receive=ack_length
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        ack=data_bytes.decode("utf-8")
        if ack=="_$invalid$_": return False
        return True
        
config_file=open("srv.cfg","r")
server_config=config_file.read()
config_file.close()
socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
socket.connect(eval(server_config))

username=input("Enter username: ")
password=input("Enter password: ")

user_config=f'("{username}",{password})'
#sending user_config str len
socket.sendall(bytes(str(len(user_config)).ljust(1024),"utf-8"))
print("User config str len sent.")

#sending user_config str 
socket.sendall(bytes(user_config,"utf-8"))
print("User config sent.")

#receiving len of response for validity of credentials
data_bytes=b''
to_receive=1024
while len(data_bytes)<to_receive:
    by=socket.recv(to_receive-len(data_bytes))
    data_bytes+=by
response_len=int(data_bytes.decode("utf-8").strip())
print("Response len received: ",response_len)

#receiving response for validity of credentials
data_bytes=b''
to_receive=response_len
while len(data_bytes)<to_receive:
    by=socket.recv(to_receive-len(data_bytes))
    data_bytes+=by
response=eval(data_bytes.decode("utf-8"))
print("Response for validity of credentials: ",response)

#taking action based on response from server
if(len(response)==1):
    print(response[0])
    socket.close()
    sys.exit()

user_uid=str(response[1])
print("User's unique-id: ",user_uid)
while True:
    request_string=input("tmclient>").strip().lower()
    if request_string[0:4]=="exit" or request_string[0:4]=="quit": 
        to_send=f'("{user_uid}","{request_string[0:4]}")'
        #sending request string length
        socket.sendall(bytes(str(len(to_send)).ljust(1024),"utf-8"))
        print("Sent request string length.")
        #sending request string
        socket.sendall(bytes(to_send,"utf-8"))
        if is_valid(socket)==False: print("Invalid user id.")
        socket.close()
        sys.exit()
    elif request_string[0:3]=="dir":
        to_send=f'("{user_uid}","{request_string[0:3]}")'
        #sending request string length
        socket.sendall(bytes(str(len(to_send)).ljust(1024),"utf-8"))
        print("Sent request string length.")
        #sending request string
        socket.sendall(bytes(to_send,"utf-8"))
        print("Sent request string.")
        if is_valid(socket)==False: 
            print("Invalid user id.")
            socket.close()
            sys.exit()
        #receiving response len
        data_bytes=b''
        to_receive=1024
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        response_length=int(data_bytes.decode("utf-8").strip())
        #receiving response
        data_bytes=b''
        to_receive=response_length
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        response=data_bytes.decode("utf-8")
        print(response)
    elif request_string[0:8]=="download":
        file_name=request_string[request_string.rfind(" ")+1:]
        print(file_name)
        to_send=f'("{user_uid}","{request_string[0:8]}",{file_name})'
        #sending request string length
        socket.sendall(bytes(str(len(to_send)).ljust(1024),"utf-8"))
        print("Sent request string length.")
        #sending request string
        socket.sendall(bytes(to_send,"utf-8"))
        print("Sent request string.")
        if is_valid(socket)==False: 
            print("Invalid user id.")
            socket.close()
            sys.exit()
        #receiving len of ack to determine if file found or not
        data_bytes=b''
        to_receive=1024
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        ack_length=int(data_bytes.decode("utf-8").strip())
        #receiving ack to determine if file found or not
        data_bytes=b''
        to_receive=ack_length
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        ack=data_bytes.decode("utf-8")
        if ack=="_$invalid$_":
            print("Invalid file name.")
            continue
        file_name=input("Save as? ").strip()
        print("Waiting for download to begin...")
        #receiving length of file
        data_bytes=b''
        to_receive=1024
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
        file_length=int(data_bytes.decode("utf-8").strip())
        print("Length of file  received as ",file_length)
        #receiving file data in chunks of 4096 bytes
        file=open(file_name,"wb")
        data_bytes=b''
        to_receive=file_length
        percent_completed=0
        while len(data_bytes)<to_receive:
            by=socket.recv(to_receive-len(data_bytes))
            data_bytes+=by
            file.write(by)
            prev=percent_completed
            percent_completed=math.ceil((len(data_bytes)*100)/to_receive)
            if prev!=percent_completed: print(percent_completed,"% downloaded...")
        file.close()
        print("File received.")
