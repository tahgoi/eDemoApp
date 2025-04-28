from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import numpy as np
import pandas as pd
import re
import shutil
import time
import os
import requests
import streamlit as st
from datetime import datetime

# Create a FastAPI app instance
app = FastAPI()

api_mysql_update = "http://127.0.0.1:3000"
api_myapi_update = "http://127.0.0.1:8801"
api_myapi_ue = "http://127.0.0.1:8810"
#api_myapi_moshell = "http://127.0.0.1:8820"
api_myapi_moshell = "http://172.30.243.98:8820"
api_myapi_sched = "http://127.0.0.1:8841"

class App_Testinfo(BaseModel):
    s_ueid: str | None = None
    s_project: str | None = None
    s_test_id: str | None = None
    s_test_count: int | None = None
    s_test_app: str | None = None
    s_path: str | None = None
    message: str | None = None

class run_test_info(BaseModel):
    s_ueid: str | None = None
    s_model: str | None = None
    s_project: str | None = None
    s_band: str | None = None
    s_test_id: str | None = None
    s_test_app: str | None = None
    s_test_count: str | None = None
    s_test_status: str | None = None
    s_test_target1: str | None = None
    s_test_target2: str | None = None
    s_test_mos1: str | None = None
    s_test_mos2: str | None = None
    s_test_mos3: str | None = None
    message: str | None = None

class App_Cellinfo(BaseModel):
    s_ueid: str | None = None
    s_rat: str | None = None
    message: str | None = None


class App_TestTrigger(BaseModel):
    s_test_time: str | None = None
    message: str | None = None

class App_TestReport(BaseModel):
    s_proj: str | None = None
    s_testid: str | None = None
    s_testidx: int | None = None
    s_app: str | None = None
    message: str | None = None

@app.get('/')
async def root():
    message = {'Description': 'App Scheduler Is Online'}
    return message

@app.post('/init_active_test')
async def init_active_test():
    #Clean-up Folder
    path_of_files = './report/active_test/'
    clean_files_in_folder(path_of_files)

    #copy template file
    temp_path = './datasets/TM500/Templates/test_report.csv'
    test_path = path_of_files + 'test_report.csv'
    shutil.copy(temp_path, test_path)
    message = {'message': 'template copied to active_test'}
    return message

@app.post('/trigger_test', response_model=App_TestTrigger)
def trigger_test(t_model : App_TestTrigger):
    print("Call Received from Main WebApp")
    # Accept Test Trigger
    m = t_model
    s_test_time = m.s_test_time
    s_message = m.message
    # Update Log to Start # -- > add : if there is an ongoing test - reject request
    print("Logging Test Request = Starting Test.....")
    path_log_test = "./report/log_test/test_log.csv"
    pd_log_test = pd.read_csv(path_log_test, index_col=False)
    pd_log_test.loc[pd_log_test['date_time'].astype(str) == s_test_time , 'status'] = "on_going"
    pd_log_test.to_csv(path_log_test, index=False)

    # Open Test Plan / Update Status
    path_plan_test = "./report/active_test/test_plan.csv"
    pd_plan_test_updated = pd.read_csv(path_plan_test)
    pd_plan_test = pd.read_csv(path_plan_test, index_col=False)
    #print(pd_plan_test)

    s_testids = pd_plan_test['Test_Code'].to_list()
    print("Test Plan...")
    print(pd_plan_test)

    print("Test Plan Running : Run Test Moshell > Test > Moshell")
    for idx in pd_plan_test.index:

        ps_row = pd_plan_test.loc[idx]

        print("Test Plan Running, Test ID", str(idx))
        #print(ps_row)
        s_ueid = ps_row['deviceid']
        prj_name = ps_row['project']
        s_testid = ps_row['Test_Code']
        s_band = ps_row['Band']
        s_service = ps_row['app_service']
        s_test_count = ps_row['test_num']
        s_test_target1 = ps_row['target_1']
        s_test_target2 = ps_row['target_2']
        s_test_mos1 = ps_row['mos_1']
        s_test_mos2 = ps_row['mos_2']
        s_test_mos3 = ps_row['mos_3']

        #Create Test Report Folder Here
        folder_name = './report/' + prj_name + '/' + s_testid + "/"
        try:
            os.mkdir('./report/' + prj_name)
            print("Test Plan Running: Created Project Folder")
        except FileExistsError:
            print("Test Plan Running: Project Folder already exists")
        try:
            os.mkdir(folder_name)
            print("Test Plan Running: Test Folder already exists")
        except FileExistsError:
            print("Test Plan Running: Test Folder already exists")


        payload_data = {'s_ueid': s_ueid, 's_project': prj_name, 's_test_id': s_testid,'s_band': s_band,
                        's_test_app': s_service,
                        's_test_count': str(s_test_count), 's_test_status': 'open', 's_test_target1': str(s_test_target1),
                        's_test_target2': str(s_test_target2),
                        's_test_mos1': s_test_mos1,
                        's_test_mos2': s_test_mos2,
                        's_test_mos3': s_test_mos3,
                        'message': s_message}

        print("Test Plan Running:Calling /run_test api")
        api_url = api_myapi_sched + "/run_test"
        response = requests.post(api_url, json=payload_data)
        if response.status_code == 200:
            print("Test completed, updating test_plan.csv ", s_testid)
            i_message = {'status': 1}
        else:
            print("Test Failed, updating test_plan.csv ", s_testid)
            i_message = {'status': 0}

        #Test Report (Test ID)
        path_testid_report = "./report/" + prj_name + "/" + s_testid + "/" + s_testid + "_results.csv"
        pdf_testid_report = pd.read_csv(path_testid_report, index_col=False)

        # Test Report (Test Plan)
        path_test_plan = "./report/active_test/test_plan.csv"
        pdf_test_plan = pd.read_csv(path_test_plan)

        print("-- x --")
        print("------------------------")
        print("Dummy Status", s_testid)
        i_message = {'status': 1}
        print("------------------------")

        if i_message['status'] == 1:                                          #Test Successfully Completed
            # Update Test ID Report:

            print("-- x --")
            print("------------------------")

            print("Test Report - TestID ", s_testid)
            print(pdf_testid_report)
            print("------------------------")

            pdf_testid_report_peak = pdf_testid_report[['result1','result2','target1','target2']].max()
            # print("-- x --")
            # print("------------------------")
            # print("Test Report Peaks ", s_testid)
            # print("Peak Values, table")
            # print("------------------------")
            print(pdf_testid_report_peak)
            kpi_result1 = pdf_testid_report_peak[0]
            kpi_result2 = pdf_testid_report_peak[1]
            kpi_target1 = pdf_testid_report_peak[2]
            kpi_target2 = pdf_testid_report_peak[3]
            # print("-- x --")
            # print("------------------------")
            # print("Peak Values, Variable")
            # print("Peak Values DL ", str(kpi_result1))
            # print("Peak Values UL ", str(kpi_result2))
            # print("------------------------")

            # print("-- x --")
            # print("------------------------")
            # print("Test Plan Report, Baseline....")
            # print(pdf_test_plan)
            # print("------------------------")

            #pd_plan_test_updated.loc[idx, 'status'] = "done"
            pdf_test_plan.loc[idx, 'status'] = "done"

            pdf_test_plan.loc[idx, 'result1'] = kpi_result1
            pdf_test_plan.loc[idx, 'result2'] = kpi_result2
            pdf_test_plan.loc[idx, 'target1'] = kpi_target1
            pdf_test_plan.loc[idx, 'target2'] = kpi_target2

            pdf_test_plan['result1'] = pdf_test_plan['result1'].replace('-', 0)
            pdf_test_plan['result2'] = pdf_test_plan['result2'].replace('-', 0)

            pdf_test_plan['status'] = np.where(((pdf_test_plan['result1'] >= pdf_test_plan['target1']) & (pdf_test_plan['result2'] >= pdf_test_plan['target2'])),"Pass","Failed")

            # print("-- x --")
            # print("------------------------")
            # print("Test Plan Report, Updated....")
            # print(pdf_test_plan)
            # print("------------------------")
        else:
            pdf_test_plan.loc[idx, 'result1'] = 0
            pdf_test_plan.loc[idx, 'result2'] = 0
            pdf_test_plan.loc[idx, 'status'] = "Failed"
            # print("------------------------")
            # print("Test Plan Report, Updated - Failed....")
            # print(pdf_test_plan)
            # print("------------------------")

        # print("-------------------")
        # print("Updating Test Plan Data")
        # print(pdf_test_plan)
        #pd_plan_test_updated.loc[(pd_plan_test_updated['result1'] > pd_plan_test_updated['target1']) & (pd_plan_test_updated['result2'] > pd_plan_test_updated['target2']), 'status'] = 'pass'
        path_plan_test = "./report/active_test/test_plan.csv"
        pdf_test_plan.to_csv(path_plan_test, index=False)

        #Active Test Plan to Playbook
    prj_name = "NPI_HW_Radio4466_B25B7B66_M01"
    testplan_name = "NPI_HW_Radio4466_B25B7B66_M01_TestPlan"
    update_pb_tp(prj_name,testplan_name)
    return

@app.post('/run_test', response_model=App_Testinfo)
async def run_test(t_model: run_test_info):
    print("Running Test, please wait - initializing variables")
    #Initialize Values
    m = t_model
    s_ueid = m.s_ueid
    s_model = m.s_test_app + '.pt'
    s_project = m.s_project
    s_band = m.s_band
    s_test_id = m.s_test_id
    s_test_app = m.s_test_app
    s_test_count = m.s_test_count
    s_test_status = m.s_test_status
    s_test_target1 = m.s_test_target1
    s_test_target2 = m.s_test_target2
    s_test_mos1 = m.s_test_mos1
    s_test_mos2 = m.s_test_mos2
    s_test_mos3 = m.s_test_mos3
    message = m.message

    print("Running Test : Cleared Temporary Files")

    s_hostname = "localhost"
    s_portnumb = 22
    s_username = "rantechdev"
    s_password = "8200Dixie"
    s_passwlmt = "Roger$RN567x"

    #Run Pre-Change : Moshell 1

    print("Running Test : Running Moshell Script 1")
    print(s_test_mos1)
    script_mos = s_test_mos1
    script_log = s_test_mos1[:-5] + "_" + s_test_id + "_pre.log"
    script_cmd = ''
    #message= 'run_test reached'
    i_message = {'status': 1}
    if script_mos != '-':
        print("Running Test : Script 1 PreTest....")
        payload_data_lmt = {'s_hostname': s_hostname, 's_portnumb': s_portnumb, 's_username': s_username, 's_password': '-', 's_passlmt': '-',
                        'script_mos': script_mos,'script_log': script_log, 'script_cmd': script_cmd, 'message': '-', 's_message': '-'}

        api_url = api_myapi_moshell + "/send_lmt_message"

        response = requests.post(api_url, json=payload_data_lmt)

        if response.status_code == 200:
            print("Running Test : Script 1 PreTest - Done!!!")
            i_message = {'status': 1}
        else:
            print("Running Test : Script 1 PreTest - Failed, Skip this Test")
            i_message = {'status': 0}
    else:
        print("Running Test : Script 1 PreTest Not Required")

    #Run Test Application

    if i_message['status'] == 1:
        print("Running Test : Running Test - App / TM 500")
        if s_ueid == 'Logs':
            print("Running Test : No Test Required")
        if s_ueid == 'TM500':
            print("Running Test : with TM500, Request Sent to TM500 Test API----WIP")
                #Project Name, TestID, campaign.xml path
        if (s_ueid != 'Logs') & (s_ueid != 'TM500'):
            print("Running Test : with UE, Request Sent to UE Test API")
            s_path = './report/'
            x_successful = 0
            for i_x in range(int(s_test_count)):
                print("Test #", str(i_x+1) + " of " + str(s_test_count))
                api_url = api_myapi_ue + "/run_app_test"
                payload_data = {'s_ueid': s_ueid, 's_project': str(s_project),'s_band': s_band, 's_test_app': str(s_test_app), 's_target1' : str(s_test_target1), 's_target2' : str(s_test_target2),
                                's_test_id': str(s_test_id), 's_test_count': int(i_x), 's_path': str(s_path),
                                'message': message}
                response = requests.post(api_url, json=payload_data)
                if response.status_code == 200:
                    print("Message Test Successful")
                    x_successful += 1
                else:
                    print("Check Inputs")
            print("Test Completed,% done = ", str(int(x_successful / int(s_test_count) * 100)))

        if s_ueid == 'TM500':
            print("Testing with TM500")

        if s_ueid == 'UE':
            print("Testing with UE")
        # Functions_App : Init > UEInfo > Run App > calculate KPI > Update SQL Database | Playbook
        # Functions_TM500 : YAML File or TM500 End Point <Close, Start, Run Campaign, Parse Data > Calculate KPI > Update SQL Database | Playbook

        print("Running Test : Test Done!")

    #Run Post-Change
    script_mos = s_test_mos3
    script_log = s_test_mos3[:-5] + "_" + s_test_id + "_post.log"
    script_cmd = ''

    if script_mos != '-':
        print("Running Test : Script 3 Revert Change....")
        api_url = api_myapi_moshell + "/send_lmt_message"
        response = requests.post(api_url, json=payload_data_lmt)

        if response.status_code == 200:
            print("Running Test : Script 3 Revert Change Done....")
            i_message = {'status': 1}
        else:
            print("Running Test : Script 3 Revert Change Failed, check....")
            i_message = {'status': 0}
    return


def update_pb_tp(s_project,test_plan_name):

    print("-------------------")
    print("Test Plan")
    path_plan_test = "./report/active_test/test_plan.csv"
    pdf_plan_test = pd.read_csv(path_plan_test, index_col=False)
    print(pdf_plan_test)

    print("-------------------")
    print("Playbook")
    path_prj = './datasets/TM500/Projects/'
    path_prj_pb = path_prj + s_project + '/00_playbook/' + s_project + '_playbook.csv'
    pdf_prj_pb = pd.read_csv(path_prj_pb, index_col=False)
    print(pdf_prj_pb)

    #Back_up Playbook & Test Plan
    print("-------------------")
    print("Saving Back-up")
    path_prj_folder =  './datasets/TM500/Projects/' + s_project + '/00_playbook/'
    pdf_plan_test.to_csv(path_prj_folder + test_plan_name + ".csv", index=False)

    # Get current date and time
    now = datetime.now()
    # Format date and time
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    str_date_time = "_" + str(current_date) + "_" + str(current_time) + "_"
    back_up_pb = path_prj_folder + "pb_backup_" + str_date_time + "_.csv"
    #back_up_pb = path_prj_folder + "pb_backup.csv"
    pdf_prj_pb.to_csv(back_up_pb, index=False)
    print("Back-up Saved")
    print(pdf_prj_pb)
    print("-------------------")

    print("Updating Playbook")

    #Test Plan to PB : TestID Band
    for index, row in pdf_plan_test.iterrows():
        #Get Values:
        #print(row)
        s_band = row.loc['Band']
        s_testid = row.loc['Test_Code']
        s_status = row.loc['status']
        s_result_1 = row.loc['result1']
        s_result_2 = row.loc['result2']

        #Save Test Result to to Playbook
        pdf_prj_pb.loc[(pdf_prj_pb['Test_Code'] == s_testid) & (pdf_prj_pb['Band'] == s_band), 'Status'] = s_status
        pdf_prj_pb.loc[(pdf_prj_pb['Test_Code'] == s_testid) & (pdf_prj_pb['Band'] == s_band), 'result1'] = s_result_1
        pdf_prj_pb.loc[(pdf_prj_pb['Test_Code'] == s_testid) & (pdf_prj_pb['Band'] == s_band), 'result2'] = s_result_2
        pdf_prj_pb.loc[(pdf_prj_pb['Test_Code'] == s_testid) & (pdf_prj_pb['Band'] == s_band), 'Achieved'] = str(s_result_1) + " | " + str(s_result_2)

    pdf_prj_pb.to_csv(path_prj_pb, index=False)
    print("Playbook Updated")
    # print(pdf_prj_pb)
    # print("-------------------")

def check_kpi_values(row):
    if (row['result1'] >= row['target1']) and (row['result2'] >= row['target2']):
        return 'Pass'
    else:
        return 'Failed'
def clean_files_in_folder(path_of_files):
    for filename in os.listdir(path_of_files):
        file_path = os.path.join(path_of_files, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    s_remarks = 'Clean-up Done'
    return s_remarks

def clean_files_in_folder(path_of_files):
    for filename in os.listdir(path_of_files):
        file_path = os.path.join(path_of_files, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    s_remarks = 'Clean-up Done'
    return s_remarks

# Add the code to run the FastAPI app directly using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("myapi_sched:app", host="127.0.0.1", port=8841, reload=True)