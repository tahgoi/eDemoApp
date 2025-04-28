import paramiko
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import time
import streamlit as st
import os
import sys
import requests

app = FastAPI()

api_mysql_update = "http://127.0.0.1:3000"
api_myapi_update = "http://127.0.0.1:8801"
api_myapi_ue = "http://127.0.0.1:8810"
api_myapi_moshell = "http://127.0.0.1:8820"
#api_myapi_moshell = "http://172.30.243.98:8820"
api_myapi_sched = "http://127.0.0.1:8841"

class App_Testinfo(BaseModel):
    s_ueid: str | None = None
    s_project: str | None = None
    s_test_id: str | None = None
    s_test_count: int | None = None
    s_test_app: str | None = None
    s_path: str | None = None
    message: str | None = None

class moshell_info(BaseModel):
    s_hostname: str | None = None
    s_portnumb: int | None = None
    s_username: str | None = None
    s_password: str | None = None
    s_passwlmt: str | None = None
    script_mos: str | None = None
    script_log: str | None = None
    script_cmd: str | None = None
    message: str | None = None

@app.get('/')
async def root():
    message = {'Description': 'Moshell API Is Online'}
    return message

@app.post('/send_lmt_message',response_model=moshell_info)
async def send_lmt_message(t_model : moshell_info):
# @app.post('/send_lmt_message')
# async def send_lmt_message():

    m = t_model
    s_hostname= m.s_hostname
    s_portnumb= m.s_portnumb
    s_username= m.s_username
    s_password= m.s_password
    s_passwlmt= m.s_passwlmt
    script_mos= m.script_mos
    script_log= m.script_log
    script_cmd= m.script_cmd
    message= m.message
    s_message= m.s_message

    s_message = 'moshell script running.... please wait....'
    print(s_message)
    print(script_mos)
    time.sleep(10)

    s_hostname = "localhost"
    s_portnumb = 22
    s_username = "rantechdev"
    s_password = "8200Dixie"
    s_passwlmt = "Roger$RN567x"
    # script_mos = ""
    # script_log = ""
    # script_cmd = ""

    s_message = connect_to_lmt(s_hostname,s_portnumb,s_username,s_password,s_passwlmt, script_mos, script_log, script_cmd)
    print("Message from LMT Request")

    if s_message['status'] == 1:
        print("Change Successful")

    if s_message['status'] == 0:
        print("Change Failed, LMT not Reachable")

    return s_message

def ssh_to_server(hostname, port, username, password, command, passw_test):
    print("SSH to Server : message from LMT")
    print(command)

    try:
        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server
        client.connect(hostname, port=port, username=username, password=password)

        # Run the command
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Print the output and error (if any)
        print("Output:\n", output)
        s_message = {'status': 1}
        if error:
            print("Error:\n", error)
            message = {'status': 0}

        # Close the connection
        client.close()

        print("SSH to Server Successful Implementation")
        print(command)

    except Exception as e:
        print(f"An error occurred: {e}")
        s_message ={'status':0}
        print("SSH to Server Error Implementation")
        print(command)

        return s_message

    print("SSH to Server Successful Implementation")
    print(s_message['status'])

    return s_message
def connect_to_lmt(S_hostname,S_port,S_username,S_password,passw_test, script_mos_path, script_log, script_cmnd):
    #Connect to LMT
    print("LMT Function : Script Sent from Post")

    print(script_mos_path)
    print(script_log)

    command = (f'/home/rantechdev/moshell/moshell 169.254.2.2 "uv com_username=rbs;uv com_password="Roger\$RN567x";"run\ {script_mos_path} {script_log}\"""')
    s_message = ssh_to_server(S_hostname, S_port, S_username, S_password, command, passw_test)

    print("LMT Function : Script Impelemented, response from LMT")
    print(s_message['status'])

    return s_message

if __name__ == "__main__":
    import uvicorn
    #uvicorn.run("myapi_moshell:app", host="127.0.0.1", port=8820, reload=True)
    uvicorn.run("myapi_moshell:app", host="172.30.243.98", port=8820, reload=True)


