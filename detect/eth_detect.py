#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import smtplib
import config
import urllib
import json
import eth_invitecode
from email.mime.text import MIMEText
from firebase import firebase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# Firebase config 
eth_firebase_url = config.eth_firebase_url
fb = firebase.FirebaseApplication(eth_firebase_url,None)

# Check how many transaction stores in firebase
def check_firebase_content(firebase_data):
    if firebase_data != None:
        for key in firebase_data:
            address = str(firebase_data[key][u'payaddress'])
            check_transactions_content(address,key,firebase_data)

    elif firebase_data == None:
        print ("Can't find any content\nSystem will redetect after 30 seconds..........")
        time.sleep(30)
        main()


def check_transactions_content(address,key_id,firebase_data):
    txs_list = get_transactions_list()
    for txs in txs_list:
        print "here"
        if txs[u'from'] == address:
            print "From:" + txs[u'from'] + "Value:" + txs[u'value']
            value_confirm = False
            if txs[u'value'] >= config.eth_fee:
                Paid = firebase_data[key_id]["Paid"]
                if Paid == "NO":
                    data = { "Paid":"YES" , "index":firebase_data[key_id]["index"] , "timestamp":firebase_data[key_id]["timestamp"] , "payaddress":firebase_data[key_id]["payaddress"] , "name":firebase_data[key_id]["name"] , "email":firebase_data[key_id]["email"]}
                    firebase_data[key_id] = data
                    fb.put(eth_firebase_url + config.eth_firebase_field, data = data, name = key_id)
                    Name = firebase_data[key_id]["name"].encode('utf-8')
                    To = firebase_data[key_id]["email"].encode('utf-8')
                    Index = firebase_data[key_id]["index"]
                    value_confirm = True
                    send_email(Name,To,Index,value_confirm,float(txs[u'value'].encode('utf-8'))/1000000000000000000)
            elif txs[u'value'] < config.eth_fee: 
                Name = firebase_data[key_id]["name"].encode('utf-8')
                Index = firebase_data[key_id]["index"]
                To = firebase_data[key_id]["email"].encode('utf-8')
                send_email(Name,To,Index,value_confirm,float(txs[u'value'].encode('utf-8'))/1000000000000000000)

# Use Ethereum APIs to get transactions list.
def get_transactions_list():
    url = "http://api.etherscan.io/api?module=account&action=txlist&address="+config.eth_address+"&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken"
    response = urllib.urlopen(url)
    txs_list = json.loads(response.read())
    return txs_list['result']

def send_email(Name,To,Index,value_confirm,value):
    print value_confirm

    DEFAULT_SMTP = config.smtp
    DEFAULT_ACCOUNT = config.emailaccount
    DEFAULT_PASSWORD = config.emailpassword

    strSmtp = DEFAULT_SMTP
    strAccount = DEFAULT_ACCOUNT
    strPassword = DEFAULT_PASSWORD

    msg = MIMEMultipart()

    if value_confirm == True:
        text = MIMEText(Name +"您好 :" 
                    + "感謝您報名「智慧城市黑客松2018」，" + "\n"
                    + "並且使用ETH進行付款，並支付了" + str(value) + "ETH" +"\n"
                    + "接下來邀請您至KKTIX登記並領取票卷，" + "\n" 
                    + "以下為您的KKTIX票卷邀請碼。" + "\n" + "\n"
                    + "邀請碼：" + eth_invitecode.invide[Index]+ "\n"
                    + "KKTIX報名網址：" + "https://alysida.kktix.cc/events/sch2018" + "\n"
                    + "關於活動的最新動態與注意事項，請關注粉絲頁或加入各通訊群組唷！" + "\n" 
                )
        msg["Subject"] = '黑客松付款成功!'
        msg["From"] = 'jyunwei@alysida.io'
        msg["To"] = To
        
    elif value_confirm == False:
        text = MIMEText("付款錯誤!" +"\n"
                    + "序號 : " + Index +"\n"
                    + "稱呼 : " + Name +"\n"
                    + "信箱 : " + To +"\n"
                    + "付款金額 : " + str(value)
                )
        msg["Subject"] = '黑客松付款成功!'
        msg["From"] = 'jyunwei@alysida.io'
        msg["To"] = To        
    
    #image = MIMEImage(img_data, name=os.path.basename("./static/jimmy.png"))
    msg.attach(text)
    #msg.attach(image)

    server = smtplib.SMTP(strSmtp)
    server.ehlo()
    server.starttls()
    server.login(strAccount, strPassword)
    server.sendmail(strAccount, To, msg.as_string())
    server.quit()
    print('Email Sent!')

def main():
    while True:
        firebase_data = fb.get(config.eth_firebase_field,None)
        check_firebase_content(firebase_data)

        time.sleep(30)

if __name__ == '__main__':
    main()


