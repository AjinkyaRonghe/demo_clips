from flask import (
    flash,
    render_template,
    redirect,
    request,
    session,
    url_for,
)
from twilio.twiml.voice_response import VoiceResponse
from ivr_phone_tree_python import app
from ivr_phone_tree_python.view_helpers import twiml
import requests
import json
import uuid
import time

user_data = {}
number_hash = {}

@app.route('/')
@app.route('/ivr')
def home():
    return render_template('index.html')

@app.route('/ivr/initialize', methods=['POST'])
def initialize():
    caller = request.form['Caller']
    print("Caller telephone number: ", caller)
    number_hash[caller] = {}
    response = VoiceResponse()
    user_data[request.form['Caller']]={'count': 0}
    user_data[request.form['Caller']].update({'Emp_id': 0})
    user_data[request.form['Caller']].update({'AEReqId': 0})
    user_data[request.form['Caller']].update({'OTP': 0})
    print(user_data)
    response.redirect(url_for('welcome'))
    return str(response)
    
@app.route('/ivr/welcome', methods=['POST'])
def welcome():
    response = VoiceResponse()
    if user_data[request.form['Caller']]['count']==0:
        response.say("Thank you for calling Automation Edge virtual assistant.")
    get_user_input_redirect(response,"Please press 1 to reset the Active Directory password",1,'menu',"POST")
    return str(response)
    
def sleep(sec,response):
    for x in range(sec):
        response.play('https://raw.githubusercontent.com/itsonlinevijay/demo_clips/master/1-second-of-silence.mp3')
    return response

@app.route('/ivr/menu', methods=['POST'])
def menu():
    ''''print("VIJAY:", request)
    print("form type:", type(request.form))
    print("ditionary:", request.form)
    for k in request.form.keys():
        print(k, request.form[k])'''

    selected_option = request.form['Digits']
    user_data[request.form['Caller']]['count']= 0
    option_actions = {'1': _reset_ad_password_get_emp_id}

    if selected_option in option_actions:
        response = VoiceResponse()
        option_actions[selected_option](response)
        return twiml(response)

    return _redirect_welcome()

@app.route('/ivr/_reset_ad_password_send_otp', methods=['POST'])
def _reset_ad_password_send_otp():
    user_data[request.form['Caller']]['count']= 0
    set_Emp_id()
    response=VoiceResponse()
    _AE_generate_OTP()
    while user_data[request.form['Caller']]['count']<2:
        response.say("Please wait, we are sending OTP on your mobile number.")
        response.play('https://raw.githubusercontent.com/itsonlinevijay/demo_clips/master/melodyloops-preview-relaxing-acoustic-0m5s-%5BAudioTrimmer.com%5D.mp3')
        Wresponse = _get_Ae_Output(user_data[request.form['Caller']]['AEReqId'])
        if Wresponse:
            WRJson=json.loads(Wresponse)
            aeotp=str(WRJson["message"])
            if aeotp:
                break
        user_data[request.form['Caller']]['count']=user_data[request.form['Caller']]['count']+1
    user_data[request.form['Caller']]['count']= 0
    get_User_OTP(response)
    user_data[request.form['Caller']]['count']= 0
    print("This is AutomationEdgeRequestId:"+str(user_data[request.form['Caller']]['AEReqId']))
    return twiml(response)
    return _redirect_welcome()

@app.route('/ivr/set_UserOTP', methods=['POST'])   
def set_UserOTP():
    response = VoiceResponse()
    global user_data
    user_data[request.form['Caller']]['OTP']=str(request.form['Digits'])
    print(user_data)
    print("set otp done")
    print(verify_otp())
    if verify_otp():
        _AD_pass_reset()
        print("Password reset request submitted")
        response.say("Your new Active Directory password has been sent to your mobile number.")
    else:
        response.say("You have entered the wrong OTP. Please try again!")
        user_data[request.form['Caller']]['count']= 0
        get_User_OTP(response)
    return twiml(response)
    
# private methods
'''def _get_Password_reset_output():
    print(AEReqId)
    Wresponse = _get_Ae_Output(AEReqId)
    print(Wresponse)
    #WRJson=json.loads(Wresponse)
    #print(WRJson["message"])'''

def _get_Ae_Request_Id(resp):
    jsonResp = json.loads(resp)
    AEReqId=jsonResp["automationRequestId"]
    return(AEReqId)

def _get_Ae_Output(AEReqId):
    sToken=_generate_AE_token()
    url = "https://ondemand.automationedge.com/aeengine/rest/workflowinstances/"+str(AEReqId)
    payload  = {}
    headers = {
    'X-session-token': sToken,
    'Content-Type': 'application/json'
    }

    response3 = requests.request("GET", url, headers=headers, data = payload)
    resp=response3.text.encode('utf8')
    jsonResp = json.loads(resp)
    Wresponse=jsonResp["workflowResponse"]
    return Wresponse

def set_Emp_id():
    global user_data
    Emp_id=request.form['Digits']
    user_data[request.form['Caller']]['Emp_id']= Emp_id

def verify_otp():
    Wresponse = _get_Ae_Output(user_data[request.form['Caller']]['AEReqId'])
    WRJson=json.loads(Wresponse)
    aeotp=str(WRJson["message"])
    User_otp = user_data[request.form['Caller']]['OTP']
    if User_otp==aeotp[-6:]:
        return True
    else:
        return False

def _reset_ad_password_get_emp_id(response):
    #getting employee id from user
    get_user_input_redirect(response,"Please enter your 6 digit employee ID",6,'_reset_ad_password_send_otp',"POST")
    
def get_user_input_redirect(response,message,number,url,method):
    while user_data[request.form['Caller']]['count']<=2:
        #if user_data[request.form['Caller']]['count']>0:
            #response.say(message="Please give an input.")
            #sleep(1,response)
        with response.gather(num_digits=number, action=url_for(url), method=method) as g:
            g.say(message=message)
            user_data[request.form['Caller']]['count']=user_data[request.form['Caller']]['count']+1
    if user_data[request.form['Caller']]['count']>2:
        response.say(message="Sorry, we didn't receive any input. Please try again later. Have a nice day!")
        response.hangup()
    return twiml(response)
        
def get_User_OTP(response):
    get_user_input_redirect(response,"Please enter your 6 digit OTP",6,'set_UserOTP',"POST")
    
def _generate_AE_token():
    url = "https://ondemand.automationedge.com/aeengine/rest/authenticate"
    payload = 'username=aecognition2&password=Admin@123'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response1 = requests.request("POST", url, headers=headers, data = payload)
    resp=response1.text.encode('utf8')
    jsonResp = json.loads(resp)
    sToken=jsonResp["sessionToken"]
    return sToken;

def _AE_generate_OTP():
    global user_data
    Emp_id = user_data[request.form['Caller']]['Emp_id']
    sToken=_generate_AE_token()

    url = "https://ondemand.automationedge.com/aeengine/rest/execute"
    payload = "{\"orgCode\":\"AECOGNITION\",\"workflowName\":\"Send OTP\",\"userId\":\"Jane Monroe\",\"sourceId\":\"SID_"+str(uuid.uuid1())+"\",\"source\":\"AutomationEdge HelpDesk\",\"responseMailSubject\":\"null\",\"params\":[{\"name\":\"employeeId\",\"value\":\""+Emp_id+"\",\"type\":\"String\",\"order\":1,\"secret\":false,\"optional\":false,\"defaultValue\":null,\"displayName\":\"Employee ID\",\"extension\":null,\"poolCredential\":false,\"listOfValues\":null},{\"name\":\"additionalInfo\",\"value\":\"{\\\"response-type\\\":\\\"chatbot\\\",\\\"conversation_details\\\":{\\\"chat_channel\\\":\\\" webchat \\\",\\\"service_url\\\":\\\"https://webchat.botframework.com/v3/conversations/JQ7t63RSIK14d3dyuYwPP8-5/activities\\\",\\\"bot_name\\\":\\\"IT-Bot\\\",\\\"user_id\\\":\\\"123456\\\",\\\"user_name\\\":\\\"AutomationEdge Demo\\\",\\\"conversation_id\\\":\\\"sgdh72938gsdf\\\",\\\"bot_id\\\":\\\"wuhe6812273gdshg\\\"}}\",\"type\":\"String\",\"order\":2,\"secret\":false,\"optional\":false,\"defaultValue\":null,\"displayName\":\"Additional Info(Chat Details in JSON)\",\"extension\":null,\"poolCredential\":false,\"listOfValues\":null}]}"
    headers = {
    'X-session-token': sToken,
    'Content-Type': 'application/json'
    }

    AE_OTP_response = requests.request("POST", url, headers=headers, data = payload)
    resp=AE_OTP_response.text.encode('utf8')
    user_data[request.form['Caller']]['AEReqId']= _get_Ae_Request_Id(resp) 

def _AD_pass_reset():
    global user_data
    Emp_id = user_data[request.form['Caller']]['Emp_id']
    sToken=_generate_AE_token()
    
    url = "https://ondemand.automationedge.com/aeengine/rest/execute"
    payload = "{\"orgCode\":\"AECOGNITION\",\"workflowName\":\"Reset Password\",\"userId\":\"Jane Monroe\",\"sourceId\":\"SID_"+str(uuid.uuid1())+"\",\"source\":\"AutomationEdge HelpDesk\",\"responseMailSubject\":\"null\",\"params\":[{\"name\":\"employeeId\",\"value\":\""+Emp_id+"\",\"type\":\"String\",\"order\":1,\"secret\":false,\"optional\":false,\"defaultValue\":null,\"displayName\":\"Employee ID\",\"extension\":null,\"poolCredential\":false,\"listOfValues\":null},{\"name\":\"additionalInfo\",\"value\":\"{\\\"response-type\\\":\\\"chatbot\\\",\\\"conversation_details\\\":{\\\"chat_channel\\\":\\\" webchat \\\",\\\"service_url\\\":\\\"https://webchat.botframework.com/v3/conversations/JQ7t63RSIK14d3dyuYwPP8-5/activities\\\",\\\"bot_name\\\":\\\"IT-Bot\\\",\\\"user_id\\\":\\\"123456\\\",\\\"user_name\\\":\\\"AutomationEdge Demo\\\",\\\"conversation_id\\\":\\\"sgdh72938gsdf\\\",\\\"bot_id\\\":\\\"wuhe6812273gdshg\\\"}}\",\"type\":\"String\",\"order\":2,\"secret\":false,\"optional\":false,\"defaultValue\":null,\"displayName\":\"Additional Info(Chat Details in JSON)\",\"extension\":null,\"poolCredential\":false,\"listOfValues\":null}]}"
    headers = {
    'X-session-token': sToken,
    'Content-Type': 'application/json'
    }

    AE_Password_Reset_response = requests.request("POST", url, headers=headers, data = payload)
    resp=AE_Password_Reset_response.text.encode('utf8')
    user_data[request.form['Caller']]['AEReqId']= _get_Ae_Request_Id(resp)
    
def _redirect_welcome():
    response = VoiceResponse()
    response.say("Returning to the main menu", voice="alice", language="en-GB")
    response.redirect(url_for('welcome'))

    return twiml(response)
