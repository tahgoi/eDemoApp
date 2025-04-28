from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import numpy as np
import pandas as pd
import re
import shutil
import streamlit as st

import subprocess
from ppadb.client import Client as AdbClient

import cv2
import datetime
import time

import os
import sys
from PIL import Image
import easyocr

from ultralytics import YOLO

import requests

# Create a FastAPI app instance
app = FastAPI()

api_mysql_update = "http://127.0.0.1:3000"
api_myapi_update = "http://127.0.0.1:8801"
api_myapi_ue = "http://127.0.0.1:8810"
api_myapi_moshell = "http://127.0.0.1:8820"
api_myapi_sched = "http://127.0.0.1:8841"

reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
class App_Testinfo(BaseModel):
    s_ueid: str | None = None
    s_project: str | None = None
    s_band: str | None = None
    s_test_id: str | None = None
    s_test_count: int | None = None
    s_test_app: str | None = None
    s_target1: str | None = None
    s_target2: str | None = None
    s_path: str | None = None
    message: str | None = None

class App_Cellinfo(BaseModel):
    s_ueid: str | None = None
    s_rat: str | None = None
    message: str | None = None

class App_TestReport(BaseModel):
    s_proj: str | None = None
    s_testid: str | None = None
    s_testidx: int | None = None
    s_app: str | None = None
    message: str | None = None

@app.get('/')
async def root():
    message = {'Description': 'UE Test API Is Online'}
    return message

@app.get('/list_ue_connected')
async def list_ues():
    test_ueids = {'-':"NoDevice"}
    devices, deviceSD, deviceID = ue_list()
    if len(deviceID) == 0:
        return {'s_out':test_ueids}
    else:
        test_ueids = deviceID
    s_out = test_ueids
    return {'s_out': s_out}

@app.get('/ue_cellinfo', response_model = App_Cellinfo)
def ue_cellinfo(t_model: App_Cellinfo):
    m = t_model
    s_ueid = m.s_ueid
    s_model = m.s_rat
    s_message = m.message
    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == s_ueid:
            s_device = device
    device = s_device
    device.shell("dumpsys telephony.registry | grep -E \"CellIdentity|CellSignalStrength\" > /sdcard/cell_info.txt")
    device.pull("/sdcard/cell_info.txt","./report/cell_info.txt")
    #ExtractCellInformation


    message = "Done with CellInfo!"
    return {'message': message}

@app.post('/run_app_test', response_model = App_Testinfo )
def load_test(t_model: App_Testinfo):
    m = t_model
    s_ueid = m.s_ueid
    s_model = m.s_test_app + '.pt'
    s_project = m.s_project
    s_band = m.s_band
    s_test_id = m.s_test_id
    s_test_app = m.s_test_app
    s_target1 = m.s_target1
    s_target2 = m.s_target2
    s_count = m.s_test_count
    s_path = m.s_path
    s_message = m.message
    print("Run Test / Run App : Message Content ")
    print(s_message)

    run_an_app(s_project,s_band, s_test_app,s_target1, s_target2, s_test_id,s_count,s_ueid,s_model,s_message)

    return

#Functions:
def run_an_app(s_pname,s_band, s_app,s_target1, s_target2,s_testid,s_count,s_ueid,s_model,message_info):
    if s_app == 'ookla':
        message = "App Run - Ookla"
        run_ookla_app(s_pname,s_band, s_app,s_target1, s_target2,s_testid,s_count,s_ueid,s_model)

    if s_app == 'voice':
        message = "VoLTE Call"
        print(message_info)
        message_info = int(message_info)
        run_volte_app(s_pname,s_band, s_app,s_testid,s_count,s_ueid,message_info)

    if s_app == 'sms':
        message = "sms"
        print(message)
        message_info = int(message_info)
        run_sms_app(s_pname,s_band, s_app,s_testid,s_count,s_ueid,s_model,message_info)

    return

def run_volte_app(s_pname,s_band, s_app,s_testid,s_count,s_ueid,message_info):

    B_NUM = int(message_info)

    print("Running Service : VoLTE, MTC number", message_info)

    # ----- Creating a Report Folder
    folder_name = './report/' + s_pname + '/' + s_testid + "/"
    try:
        os.mkdir('./report/' + s_pname)
        print("Project Folder Created")
    except FileExistsError:
        print("Project Folder Exist, no Action")

    try:
        os.mkdir(folder_name)
        print("Test Folder Created")

    except FileExistsError:
        print("Test Folder Exist, no Action")

    # Initialize DataFrame
    f_fields = ['test_device', 'cell_bw', 'cell_pci', 'pcc_rsrp', 'pcc_sinr', 'project', 'band', 'testid', 'test_app',
                'test_refid', 'status', 'result1', 'result2', 'target1', 'target2', 'kpi1', 'kpi2', 'remarks']
    f_values = [s_ueid, '20Mhz', '999', '-111', '-30', s_pname, s_band, s_testid, s_app,
                s_count, 'done', 0, 0, 3, 3, 'VoLTE MoC', 'VoLTE MTC', '']

    rep_df = pd.DataFrame([f_values], columns=f_fields)

    pfd_report = folder_name + s_testid + '_results.csv'
    rep_df.to_csv(pfd_report, index=False)

    csv_files = []
    kpi_value = []

    # Copy Cell Info to Test Folder
    shutil.copy("./report/cell_info.txt", folder_name)

# ----- Start Application
    print("Starting VoLTE Call Test......")

    ue_home(s_ueid)
    message = "UE Home"
    print(message)
    time.sleep(0.5)

    ue_voice_moc(s_ueid,B_NUM,s_count,s_pname,s_testid,folder_name)
    message = "UE Home"
    print(message)
    time.sleep(0.5)


def run_ookla_app(s_pname,s_band, s_app,s_target1, s_target2, s_testid,s_count,s_ueid,s_model):

# ----- Creating a Report Folder
    folder_name = './report/' + s_pname + '/' + s_testid + "/"
    try:
        os.mkdir('./report/' + s_pname)
        print("Project Folder Created")
    except FileExistsError:
        print("Project Folder Exist, no Action")

    try:
        os.mkdir(folder_name)
        print("Test Folder Created")

    except FileExistsError:
        print("Test Folder Exist, no Action")

    #Initialize DataFrame
    f_fields = ['test_device', 'cell_bw', 'cell_pci','pcc_rsrp', 'pcc_sinr','project','band','testid','test_app','test_refid','status','result1','result2','target1','target2','kpi1','kpi2','remarks']
    f_values = [s_ueid, '20Mhz', '999', '-111', '-30', s_pname, s_band, s_testid,s_app,
                        s_count, 'done', 0, 0, s_target1, s_target2, 'DL Thp', 'UL Thp', '']

    rep_df = pd.DataFrame([f_values], columns=f_fields)

    csv_files = []
    kpi_value = []

    #Copy Cell Info to Test Folder
    cell_info_name = folder_name + "cell_info_" + s_testid + ".csv"
    shutil.copy("./report/cell_info.txt", cell_info_name)

#----- Start Application
    print("Starting Ookla Test......")
    message = s_ueid
    ue_up(s_ueid)
    message = "UE Up"
    print(message)
    time.sleep(0.5)

    ue_home(s_ueid)
    message = "UE Home"
    print(message)
    time.sleep(0.5)

    ue_killapp(s_ueid,'org.zwanoo.android.speedtest')
    message = "App Deactivated"
    print(message)
    time.sleep(0.5)

    ue_home(s_ueid)
    message = "UE Home"
    print(message)
    time.sleep(0.5)

    ue_openapp(s_ueid,'org.zwanoo.android.speedtest')
    message = "App Activated"
    print(message)
    time.sleep(0.5)

    if s_target1 == '-':
        s_target1 = 0
    else:
        s_target1 = int(s_target1)

    if s_target2 == '-':
        s_target2 = 0
    else:
        s_target2 = int(s_target2)



    izx = s_count

    # 4. Detect if UE Ready for Testing
    time.sleep(5)
    s_img_id = ['ookla_ready']
    max_count = 30
    message_base = "Search ookla test ready, "
    message, px, py = run_search_image_tap(s_ueid, s_model, s_img_id, max_count, message_base)

    print(message)

    if px == -1:
        s_img_id = ['ookla_testagain']
        max_count = 10
        message_base = "Search Test Again "
        message, px, py = run_search_image_tap(s_ueid, s_model, s_img_id, max_count, message_base)
        print(message)

    if px == -1:
        message = "Test Failed, Ready/Test Again not Found" + str(s_count)
        print(message)
        sys.exit(0)

    message = "Test Starting...." + str(s_count)
    print(message)
    time.sleep(10) #Wait and check of Test Really Starts

    #Optimize this with Multiple Detections
    for i_s in range(10):
        s_img_id = ['ookla_testdetails']
        max_count = 1
        message_base = "Search for Test Details"
        message, px, py = run_search_image_tap(s_ueid, s_model, s_img_id, max_count, message_base)
        print(message)
        print("Searching for end", str(i_s))

        if px == -1:
            s_img_id = ['ookla_testagain']
            max_count = 1
            message_base = "Search for Test Again"
            message, px, py = run_search_image_notap(s_ueid, s_model, s_img_id, max_count, message_base)
            print(message)

        if px != -1:
            message_base = "Search End Detected"
            print(message)
            time.sleep(1)
            break
        else:
            message_base = "Search End no detected"
            print(message)

    #if End of Test is not detected
    if px == -1:
        message_base = "Search for UL KPI"
        s_img_id = ['ookla_ul']
        max_count = 2
        message, px, py = run_search_image_notap(s_ueid, s_model, s_img_id, max_count, message_base)
        print(message)
        time.sleep(0)

    if px != -1:
        message = "Test UL Found, Check if any Value Saved!" + str(s_count)
        print(message)
        save_frame = './temp/obj_found_ookla_ul.png'
        if not os.path.isfile(save_frame):
            print('Object Not Found ', save_frame)
            sys.exit(0)
        else:
            print('Object Found ', save_frame)
            s_img = cv2.imread(save_frame)
            results = reader.readtext(s_img)
            extracted_text = ' '.join([text[1] for text in results])
            print(extracted_text)
            kpi_value_ul = extract_numbers(extracted_text)
            print("UL Thp = " + str(kpi_value_ul))
            time.sleep(1)


    if (px != -1) & (len(str(kpi_value_ul))!= 0):
        message = "Test Sucessful, saving result" + str(s_count)
        print(message)

        #Test Report
        p_path = folder_name
        s_band_testid = s_band + "_" + s_testid
        f_path, f_name= save_screen_project(s_ueid, s_pname, s_band_testid, s_count, p_path)
        time.sleep(1)
        lst_imgs = ['ookla_dl','ookla_ul','ookla_testid']
        for index, lst_img in enumerate(lst_imgs):
            kpi_value.append(0)
            save_frame = './temp/obj_found_'+lst_img +'.png'
            if not os.path.isfile(save_frame):
                print('Object Not Found ', save_frame)
            else:
                print('Object Found ', save_frame)
                s_img = cv2.imread(save_frame)
                results = reader.readtext(s_img)
                extracted_text = ' '.join([text[1] for text in results])
                print(extracted_text)
                kpi_value[index] = extract_numbers(extracted_text)
                print(lst_img + " = " + str(kpi_value[index]))
        message = "Screenshot Saved"

        rep_df['result1'] = kpi_value[0]
        rep_df['result2'] = kpi_value[1]
        rep_df['target1'] =rep_df['target1'].astype(float)
        rep_df['target2'] =rep_df['target2'].astype(float)

        rep_df['result1'] = rep_df['result1'].replace('-', 0)
        rep_df['result2'] = rep_df['result2'].replace('-', 0)

        rep_df['status'] = np.where(((rep_df['result1'] >= rep_df['target1']) & (rep_df['result2'] >= rep_df['target2'])), "Pass", "Failed")

        pfd_report = folder_name + s_testid + '_results.csv'

        if izx == 0:
            f_kpi_df = rep_df
            f_kpi_df.to_csv(pfd_report, index=False)
        else:
            f_kpi_df = pd.read_csv(pfd_report)
            merge_kpi = pd.concat([f_kpi_df,rep_df],ignore_index=True)

            print("Merged Data")
            print(merge_kpi)
            merge_kpi.to_csv(pfd_report, index=False)


        f_kpi_df = pd.DataFrame()
        time.sleep(2)
        px = -1
        py = -1
        message = "Successful : Image & CSV Saved!"

    return

def run_sms_app(s_pname,s_band,s_app,s_testid,s_count,s_ueid,s_model,message_info):
    B_NUM = int(message_info)

    print("Running Service : SMS, MTC number", message_info)

    # ----- Creating a Report Folder
    folder_name = './report/' + s_pname + '/' + s_testid + "/"
    try:
        os.mkdir('./report/' + s_pname)
        print("Project Folder Created")
    except FileExistsError:
        print("Project Folder Exist, no Action")

    try:
        os.mkdir(folder_name)
        print("Test Folder Created")

    except FileExistsError:
        print("Test Folder Exist, no Action")

    # Initialize DataFrame
    f_fields = ['test_device', 'cell_bw', 'cell_pci', 'pcc_rsrp', 'pcc_sinr', 'project', 'band', 'testid', 'test_app',
                'test_refid', 'status', 'result1', 'result2', 'target1', 'target2', 'kpi1', 'kpi2', 'remarks']
    f_values = [s_ueid, '20Mhz', '999', '-111', '-30', s_pname, s_band, s_testid, s_app,
                s_count, 'done', 0, 0, 3, 3,'SMS MoC', 'SMS MTC', '']

# ----- Start Application
    print("Starting SMS Test......")

    ue_home(s_ueid)
    message = "UE Home"
    print(message)
    time.sleep(0.5)

    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == s_ueid:
            s_device = device
    device = s_device

    s_img_id = ['app_sms']
    max_count = 10
    message_base = "to Send SMS "
    message, px, py = run_search_image_tap(s_ueid, s_model, s_img_id, max_count, message_base)
    print(message)
    time.sleep(3)

    if px == -1:
        message = "SMS App Not Found, no Screenshot" + str(s_count)
        print(message)
        sys.exit(0)


    p_path = folder_name
    s_band_testid  = s_band + "sms_mos_pretest_"
    save_screen_project(s_ueid, 'sms', s_band_testid , s_count, './report/' + s_pname + '/' + s_testid + '/')

    time.sleep(3)

    device.shell(f'am start -a android.intent.action.SENDTO -d sms:{B_NUM} --es sms_body \"Test SMS from MOC {s_testid}_{s_count}\" --ez exit_on_sent true')

    time.sleep(3)

    s_img_id = ['sms_send']
    max_count = 10
    message_base = "to Send SMS "
    message, px, py = run_search_image_tap(s_ueid, s_model, s_img_id, max_count, message_base)
    print(message)
    time.sleep(3)

    if px == -1:
        message = "SMS App Not Found, no Screenshot" + str(s_count)
        print(message)
        sys.exit(0)
    else:
        message = "SMS Sent" + str(s_count)
        print(message)

    time.sleep(5)
    s_band_testid = s_band + "sms_mos_pretest_"
    save_screen_project(s_ueid, 'sms', s_band_testid, s_count, './report/' + s_pname + '/' + s_testid + '/')

    time.sleep(3)

    return

def check_kpi_values(row):
    if (row['result1'] >= row['target1']) and (row['result2'] >= row['target2']):
        return 'Pass'
    else:
        return 'Failed'

def ue_list():
    deviceSD = []
    deviceID = {}
    devices = []
    try:
        adb = AdbClient(host="127.0.0.1", port=5037)
        devices = adb.devices()
        for device in devices:
            device_serial = device.serial
            deviceSD.append(device_serial)
            deviceID[device_serial] = device
            print("Devices",device)
    except Exception:
        print("Error, no android device connected...")
        return devices, deviceSD, deviceID
    return devices, deviceSD, deviceID

def adb_ue_screenshot(i_device):
    devices, deviceSD, deviceID = ue_list()
    p_image = './view/active_screen.png'
    for device in devices:
        if device.serial == i_device:
            s_device = device
    device = s_device
    device.shell("screencap -p /sdcard/screen.png")
    time.sleep(0.5)
    device.pull("/sdcard/screen.png", "./view/active_screen.png")
    return p_image

def ue_up(i_device):
    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == i_device:
            s_device = device
    device = s_device
    return device

def ue_home(i_device):
    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == i_device:
            s_device = device
    device = s_device
    device.shell('input keyevent 3')
    screen_page = "HomeScreen"
    return screen_page

def ue_killapp(i_device,i_app):
    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == i_device:
            s_device = device
    device = s_device

    device.shell('input keyevent KEYCODE_APP_SWITCH')
    time.sleep(1)

    device.shell('input keyevent KEYCODE_CLEAR')
    time.sleep(1)

    device.shell('am kill-all')
    time.sleep(1)

    #device.shell('am kill org.zwanoo.android.speedtest')
    device.shell(f'am kill {i_app}')
    time.sleep(1)

    #device.shell('am force-stop org.zwanoo.android.speedtest')
    device.shell(f'am force-stop {i_app}')
    time.sleep(1)

    screen_page = "HomeScreen"
    return screen_page

def ue_voice_moc(s_ueid,B_NUM,s_count,s_pname,s_testid,folder_name):

    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == s_ueid:
            s_device = device
    device = s_device

    device.shell(f'am start -a android.intent.action.CALL -d tel:{B_NUM} ')
    time.sleep(5)
    device.shell("dumpsys telephony.registry | grep \"mCallState\" > /sdcard/cell_info_voice_ongoing.txt")
    device.pull("/sdcard/cell_info_voice_ongoing.txt","./report/cell_info_voice_ongoing.txt")

    time.sleep(12)
    s_band_testid =  "volte_moc_pretest_"
    save_screen_project(s_ueid, 'voice_call', s_band_testid , s_count,'./report/' + s_pname + '/' + s_testid+ '/')

    time.sleep(3)

    device.shell('input keyevent KEYCODE_ENDCALL')

    time.sleep(3)

    device.shell("dumpsys telephony.registry | grep \"mCallState\" > /sdcard/cell_info_voice_end.txt")
    device.pull("/sdcard/cell_info_voice_end.txt","./report/cell_info_voicecall_end.txt")

    folder_name_file = folder_name + "cell_info_voice_ongoing_" + str(s_count) + ".csv"
    shutil.copy("./report/cell_info_voice_ongoing.txt", folder_name_file)

    folder_name_file =folder_name + "cell_info_voicecall_end_" + str(s_count) + ".csv"
    shutil.copy("./report/cell_info_voicecall_end.txt", folder_name_file)

    return


def ue_openapp(i_device,i_app):
    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == i_device:
            s_device = device
    device = s_device

    device.shell(f'monkey -p {i_app} -c android.intent.category.LAUNCHER 1')
    time.sleep(1)

    return

def run_search_image_tap(s_ueid,s_model,s_img_id,max_count,message_base):
    adb_ue_screenshot(s_ueid)
    px, py = run_search_image(s_ueid, s_model, s_img_id, max_count)
    if px != -1:
        cv_click(px, py, s_ueid)
        message = message_base + "  found & tap"
    else:
        message = message_base + "  not found"
    return message, px, py

def run_search_image_notap(s_ueid,s_model,s_img_id,max_count,message_base):
    adb_ue_screenshot(s_ueid)
    px, py = run_search_image(s_ueid, s_model, s_img_id, max_count)
    if px != -1:
        message = message_base + "  found & tap"
    else:
        message = message_base + "  not found"
    return message, px, py

def run_search_image(s_ueid,s_model,s_img_id,max_count):
    x_stop = False
    s_type = 'adb'
    px = -1
    py = -1
    x_count = 0

    while x_stop != True:
        adb_ue_screenshot(s_ueid)
        p_img = './view/active_screen.png'

        print("Loop " + str(x_count))
        detected_lst_classid, detected_lst_locid, detected_lst_conf = model_testing(s_model, p_img, s_type)
        print("Location ID")
        print(detected_lst_locid)
        found_lst_classid, found_lst_locidx, found_lst_locidy = location_obj_center(detected_lst_classid,detected_lst_locid,detected_lst_conf,s_img_id)
        message = "run search image- Test model / found"
        i_count = 0
        for  i_img_id in  s_img_id:
            for i_class_id in found_lst_classid:
                if i_class_id == i_img_id:
                   px = int(found_lst_locidx[i_count])
                   py = int(found_lst_locidy[i_count])
                   x_stop = True
                   print("Image Found!!!",str(int(px)) + "_" + str(int(py)))
                i_count +=1

        x_count +=1
        if x_count >= max_count:
            x_stop = True
            print("Test Failed, Image not found -Cause : TimeOut!")
            message = "Test Failed, Image not found -Cause : TimeOut!"
        else:
            message = "Test Successful, Image found!"

    return px, py

def location_obj_center(detected_lst_classid, detected_lst_locid, detected_lst_conf,s_obj):

    s_obj_found = []
    s_loc_found = []
    s_cnf_found = []

    s_obj_foundy = []
    s_loc_foundy = []
    s_cnx_foundy = []
    s_cny_foundy = []

    for i_obj in s_obj:
        i_count = 0
        #st.write("Searching for ",i_obj)
        for i in detected_lst_classid:
            #st.write("Comparing for ", i_obj + "-" + i )
            if i_obj == i:
                s_obj_found.append(i_obj)
                s_loc_found.append(detected_lst_locid[i_count])
                s_cnf_found.append(detected_lst_conf[i_count])
            i_count += 1
    if len(s_obj_found) != 0:
        # Convert Found Object to Data Frame
        s_obj_df = pd.DataFrame({'Class': s_obj_found, 'Confidence': s_cnf_found, 'Location': s_loc_found})
        # Remove Duplicate Class & Get the best Confidence
        s_obj_df_pvt = s_obj_df.pivot_table(values='Confidence', index='Class', aggfunc='max')
        s_obj_df_pvt = s_obj_df_pvt.reset_index()
        s_obj_foundy = s_obj_df_pvt['Class'].to_list()
        s_cnf_foundy = s_obj_df_pvt['Confidence'].to_list()


        # Recover Location
        y_count = 0
        for i_obj in s_obj_foundy:
            x_count = 0
            for i in s_obj_found:
                if i_obj == i:
                    if s_cnf_foundy[y_count] == s_cnf_found[x_count]:
                        s_loc_foundy.append(s_loc_found[y_count])
                x_count += 1
            y_count += 1

        # Extract Object Center Location:

        for s_loc in s_loc_foundy:
            xmin, ymin, xmax, ymax = s_loc.astype(float)
            s_cnx_foundy.append(xmin + (xmax - xmin) / 2)
            s_cny_foundy.append(ymin + (ymax - ymin) / 2)

        if len(s_cnx_foundy) != 0:
            print("Class Found",s_cnx_foundy)
            kpi_lists = ['ookla_dl', 'ookla_ul']
            i_dx = 0
            for s_obj in s_obj_foundy:
                save_frame = './temp/obj_found_' + s_obj + '.png'
                img = Image.open(save_frame)
                # Show Frame in WebApp
                print(s_obj)
                #st.image(img)
                if s_obj in kpi_lists:
                    img = cv2.imread(save_frame)

                    results = reader.readtext(save_frame)
                    extracted_text = ' '.join([text[1] for text in results])
                    print(extracted_text)
    else:
        print("Object Selected Not Found",s_cnx_foundy)

    return s_obj_foundy, s_cnx_foundy, s_cny_foundy

def cv_click(px, py, i_device):
    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == i_device:
            s_device = device
    device = s_device
    print("Device",device)
    device.shell('input tap ' + str(px) + ' ' + str(py))
    s_status=5
    return s_status

def save_screen_project(s_ueid,s_prj,s_testid,i, p_path):

    devices, deviceSD, deviceID = ue_list()
    for device in devices:
        if device.serial == s_ueid:
            s_device = device
    device = s_device
    f_name = s_testid +"_"+ str(i) + ".png"
    f_path = p_path + f_name
    print(f_path)
    device.shell("screencap -p /sdcard/screen.png")

    device.pull("/sdcard/screen.png", f_path)
    return f_path, f_name

def clean_files_in_folder(path_of_files):
    for filename in os.listdir(path_of_files):
        file_path = os.path.join(path_of_files, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    s_remarks = 'Clean-up Done'
    return s_remarks

def model_testing(s_model,p_img,s_type):

    img_source = p_img

    model_path = './models/' + s_model

    print("--------------------Model Path")
    print(model_path)
    print("--------------------")

    print("--------------------Clean Buffer ./temp")
    temp_path = './temp/'
    s_remarks = clean_files_in_folder(temp_path)
    print(s_remarks)
    print("--------------------")

    detected_lst_classid = []
    detected_lst_locid =[]
    detected_lst_conf =[]

    #img_source = 'folder'
    min_thresh = 0.5
    user_res = '640x480'
    #record = args.record

    # Check if model file exists and is valid
    print(model_path)
    if (not os.path.exists(model_path)):
        print('ERROR: Model path is invalid or model was not found. Make sure the model filename was entered correctly.')
        sys.exit(0)

    # Load the model into memory and get labemap
    print("--------------------Load Model to Yolo")
    model = YOLO(model_path, task='detect')
    labels = model.names
    print("--------------------")

    # Set bounding box colors (using the Tableu 10 color scheme)
    bbox_colors = [(164, 120, 87), (68, 148, 228), (93, 97, 209), (178, 182, 133), (88, 159, 106),
                   (96, 202, 231), (159, 124, 168), (169, 162, 241), (98, 118, 150), (172, 176, 184)]

    print('Load Frame')
    frame = cv2.imread(img_source)
    print('Run Inference')
    # Run inference on frame
    results = model(frame, verbose=False)

    print('Extract Results')
    # Extract results
    detections = results[0].boxes
    # Initialize variable for basic object counting example
    object_count = 0

    print('Boxing Objects')
    # Go through each detection and get bbox coords, confidence, and class
    for i in range(len(detections)):
        # Get bounding box coordinates
        # Ultralytics returns results in Tensor format, which have to be converted to a regular Python array
        xyxy_tensor = detections[i].xyxy.cpu()  # Detections in Tensor format in CPU memory
        xyxy = xyxy_tensor.numpy().squeeze()  # Convert tensors to Numpy array
        xmin, ymin, xmax, ymax = xyxy.astype(int)  # Extract individual coordinates and convert to int

        # Get bounding box class ID and name
        classidx = int(detections[i].cls.item())
        classname = labels[classidx]
        # Get bounding box confidence
        conf = detections[i].conf.item()

        # Draw box if confidence threshold is high enough

        conf_threshold = 0.5

        if conf > conf_threshold:
            detected_lst_classid.append(classname)
            detected_lst_locid.append(xyxy)
            detected_lst_conf.append(conf)
            color = bbox_colors[classidx % 10]
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)

            label = f'{classname}: {int(conf * 100)}%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)  # Get font size
            label_ymin = max(ymin, labelSize[1] + 10)  # Make sure not to draw label too close to top of window
            cv2.rectangle(frame, (xmin, label_ymin - labelSize[1] - 10),
                          (xmin + labelSize[0], label_ymin + baseLine - 10), color,
                          cv2.FILLED)  # Draw white box to put label text in
            cv2.putText(frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0),
                        1)  # Draw label text

            #Save Image Found
            # Define the bounding box (left, upper, right, lower)

            # Crop the image using the bounding box
            save_frame_path = './temp/obj_detected_' + classname + '.png'
            save_frame = 'obj_detected_' + classname + '.png'
            cv2.imwrite(save_frame_path, frame)

            image = cv2.imread(save_frame_path)

            # Define the bounding box (x, y, width, height)
            x, y, w, h = xmin, ymin, xmax, ymax

            x = xmin
            y = ymin
            w = xmax
            h = ymax

            # Crop the image using the bounding box
            cropped_image = image[y:h, x:w]

            # Save the cropped image
            cv2.imwrite('./temp/obj_found_' + classname + '.png', cropped_image)

            # Basic example: count the number of objects in the image
            object_count = object_count + 1
    # Display detection results
    cv2.putText(frame, f'Number of objects: {object_count}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255),
                2)  # Draw total number of detected objects

    cv2.imwrite('./view/active_screen_marked.png', frame)

    return detected_lst_classid, detected_lst_locid, detected_lst_conf

def extract_numbers(extracted_text):
    numbers  = re.findall(r'\d+\.\d+|\d+',extracted_text)
    return float(''.join(numbers)) if numbers else 0

# Add the code to run the FastAPI app directly using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("myapi_ue:app", host="127.0.0.1", port=8810, reload=True)