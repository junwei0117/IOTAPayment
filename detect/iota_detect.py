#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys 
sys.path.append('') 
import random
import time
import smtplib
import config
import inviteCode
from iota import *
from email.mime.text import MIMEText
from firebase import firebase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

#IOTA config
node_url = config.iota_node_url
seed = config.iota_seed
Fee = config.iota_fee

#Firebase config
firebase_url = config.iota_firebase_url
iota_db = firebase.FirebaseApplication(firebase_url,None)

# Check how many transaction stores in firebase
def check_firebase_content(firebase_data):
    if firebase_data != None:
        count = len(firebase_data)
    elif firebase_data == None:
        count = 0
    return count

# Find the key index of specific transaction
def find_key_index(address,firebase_data):
    key_id=""
    if firebase_data != None:
        for key in firebase_data:
            if str(firebase_data[key][u'payaddress']) == address :
                key_id = key
    return key_id

# If there isn't any content in firebase, show the issues
def none_content(Count):
    if Count == 0:
        print ("Can't find any content")
        print ("-----------------------------------------------\nSystem will redetect after 30 seconds..........")
        time.sleep(30)
        main()

# Confirm the addresses has been paid or not. 
# If the address has been payment , send a confirmed letter, 
# otherwise continue to detect the next one.
def scan_addresses(Count,firebase_data):
    api = Iota(node_url, seed)
    NewAddress = api.get_new_addresses(index=1, count=Count,checksum=True)['addresses']
    i = 0
    for line in firebase_data:
        address = [NewAddress[i]]
        balance = balances_detect(address)
        print ("Index : " + str(i+1) + " address : " + str(address[0]) + " : " + str(balance))
        if balance == Fee:
            key_id = find_key_index(address[0],firebase_data)
            Paid = firebase_data[key_id]["Paid"]
            if Paid == "NO":
                data = { "Paid":"YES" , "index":firebase_data[key_id]["index"] , "timestamp":firebase_data[key_id]["timestamp"] , "payaddress":firebase_data[key_id]["payaddress"] , "name":firebase_data[key_id]["name"] , "email":firebase_data[key_id]["email"]}
                firebase_data[key_id] = data
                iota_db.put(firebase_url + config.iota_firebase_field, data = data, name = key_id)
                Name = firebase_data[key_id]["name"].encode('utf-8')
                To = firebase_data[key_id]["email"].encode('utf-8')
                Index = firebase_data[key_id]["index"]
                #SerialNum = firebase_data[key_id]['index']
                send_email(Name,To,Index)
        i += 1             
    print ("-----------------------------------------------\nSystem will re-detect after 30 seconds..........")

# Sends a request to the IOTA node and gets the current confirmed balance
def balances_detect(address):
    api = Iota(node_url)
    gb_result = api.get_balances(address)
    balance = gb_result['balances']
    return (balance[0])

# Send a confirmed letter.
def send_email(Name,To,Index):

    DEFAULT_SMTP = config.smtp
    DEFAULT_ACCOUNT = config.emailaccount
    DEFAULT_PASSWORD = config.emailpassword

    strSmtp = DEFAULT_SMTP
    strAccount = DEFAULT_ACCOUNT
    strPassword = DEFAULT_PASSWORD

    #SerialNum = "%03d" % SerialNum

    #img_data = open("./static/jimmy.png", 'rb').read()
    msg = MIMEMultipart()
    text = MIMEText(Name +"您好 :" 
                    + "感謝您報名「智慧城市黑客松2018」，" + "\n"
                    + "並且使用IOTA進行付款，" + "\n"
                    + "接下來邀請您至KKTIX登記並領取票卷，" + "\n" 
                    + "以下為您的KKTIX票卷邀請碼。" + "\n" + "\n"
                    + "邀請碼：" + inviteCode.invide[Index]+ "\n"
                    + "KKTIX報名網址：" + "https://alysida.kktix.cc/events/sch2018" + "\n"
                    + "我們會將資料轉發給此次有人才招募需求的合作徵才管道。" + "\n"
                    + "關於活動的最新動態與注意事項，請關注粉絲頁或加入各通訊群組唷！" + "\n" 
    )
    
    #image = MIMEImage(img_data, name=os.path.basename("./static/jimmy.png"))
    msg.attach(text)
    #msg.attach(image)
    
    msg["Subject"] = '黑客松付款成功!'
    msg["From"] = 'jyunwei@alysida.io'
    msg["To"] = To

    server = smtplib.SMTP(strSmtp)
    server.ehlo()
    server.starttls()
    server.login(strAccount, strPassword)
    server.sendmail(strAccount, To, msg.as_string())
    server.quit()
    print('Email Sent!')

def main():
    while True:
        firebase_data = iota_db.get(config.iota_firebase_field,None)
        print ("\nDetecting Registrants..........") 
        Count = check_firebase_content(firebase_data)
        none_content(Count)
        scan_addresses(Count,firebase_data)
        time.sleep(30)
            
if __name__ == '__main__':
    main()
