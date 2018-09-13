#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flask import Flask, render_template, flash, request,send_file
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from iota import *
from random import SystemRandom
from flask import Markup
from firebase import firebase
import random
import os
import config
import qrcode
import sys
import time

reload(sys)
sys.setdefaultencoding("utf-8")

# firebase config
iota_firebase_url = config.iota_firebase_url
iota_db = firebase.FirebaseApplication(iota_firebase_url,None)
eth_firebase_url = config.eth_firebase_url
eth_db = firebase.FirebaseApplication(eth_firebase_url,None)

# IOTA config
iota_node_url = config.iota_node_url
iota_seed = config.iota_seed
api = Iota(iota_node_url,iota_seed)
 
# App config
app=Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY']='j7rjif6ik3nh89gss'
app.debug = True

# QRcode config
qr = qrcode.QRCode(
    version = 1,
    error_correction = qrcode.constants.ERROR_CORRECT_H,
    box_size = 10,
    border = 4,
    )

# Check the current transaction index for next transaction index.
def check_tx_index(firebase_data):
    if firebase_data != None:
        index = len(firebase_data) + 1
    elif firebase_data == None:
        print firebase_data
        index = 1
    return index

# Check the email address has been used or not from firebase.
def check_email_used(email,firebase_data):
    if firebase_data != None:
        for key in firebase_data:
            if  str(firebase_data[key][u'email']) == email:
                check =  False
                break
            else:
                check = True
        return check
    elif firebase_data == None:
        check = True
        return check

# Generate a pay address QRcode for trinity wallet
def generate_QRcode(rowdata):
    trinitydata ="{\"address\":"+"\""+rowdata+"\""+",\"amount\": \""+str(config.iota_fee)+"\""+", \"message\": \""+config.trinity_messageInTxs+"\",\"tag\": \"\"}"
    qr.add_data(trinitydata)
    qr.make(fit=True)
    img = qr.make_image()
    img.save("./static/trinity.jpg")
    qr.clear()

# Generate a new address
def generate_new_address(index):
    address =  api.get_new_addresses(index=index,checksum=True)
    return  address

# Record the registration time.
def timestamp():
    localtime = time.asctime( time.localtime(time.time()))
    return localtime

# Store the registration message on firebase.
def push_to_firebase(index,timestamp,payaddress,name,email,crypt):
    if crypt == "IOTA":
        RegData = {"Paid":"NO","index":index,"timestamp":timestamp,"payaddress":payaddress,"name":name,"email":email}
        iota_db.post(config.iota_firebase_field,RegData)
        print "Firebase Save success"
    elif crypt =="ETH":
        RegData = {"Paid":"NO","index":index,"timestamp":timestamp,"payaddress":payaddress,"name":name,"email":email}
        eth_db.post(config.eth_firebase_field,RegData)
        print "Firebase Save success"

# Check the tranasction status from firebase
def check_tx_status(email,firebase_data):
    key_id=""
    result = ["NOTFOUND"]
    if firebase_data != None:
        for key in firebase_data:
            if str(firebase_data[key][u'email']) == email :
                key_id = key
                result = [firebase_data[key_id]["Paid"],firebase_data[key_id]["name"],firebase_data[key_id]["email"],firebase_data[key_id]["payaddress"],firebase_data[key_id]["timestamp"]]
        return result

# reattach to tangle
def reattach(txhash):
    
    depth = 2
    magnitute = 14

    try:
        api.replay_bundle(txhash, depth, magnitute)

    except Exception as e:
        error = "\nERROR: %s\n" % e
        return error
        
    finally:
        success = "成功 !"
        return success

class iota_registration_form(Form):
    name = TextField('Name:', validators=[validators.required()])
    email = TextField('Email:', validators=[validators.required(), validators.Length(min=6, max=35)])

class reattch_form(Form):
    txhash = TextField('Txhash:', validators=[validators.required()])

class check_status_form(Form):
    regemail = TextField('Regemail:', validators=[validators.required(), validators.Length(min=6, max=35)])

class eth_registration_form(Form):
    name = TextField('Name:', validators=[validators.required()])
    email = TextField('Email:', validators=[validators.required(), validators.Length(min=6, max=35)])
    eth_address = TextField('eth_address:', validators=[validators.required(), validators.Length(min=30, max=36)])

class eth_check_status_form(Form):
    regemail = TextField('Regemail:', validators=[validators.required(), validators.Length(min=6, max=35)])

@app.route("/", methods=['GET', 'POST'])
def payment():
    form = iota_registration_form(request.form)
    print form.errors

    if request.method == 'POST':
        name=request.form['name']
        email=request.form['email']

        if form.validate():

            firebase_data = iota_db.get(config.iota_firebase_field,None)
            check = check_email_used(email,firebase_data)
            if check == True :
                index = check_tx_index(firebase_data)
                pay_address = str(generate_new_address(index)[u'addresses'][0])
                generate_QRcode(pay_address)
                push_to_firebase(index,timestamp(),pay_address,name.encode('utf-8'),email.encode('utf-8'),"IOTA")
                message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"報名成功 !"+"</dt>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"請依照下面的地址進行付款"+"</dt>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"姓名:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+name+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"信箱:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+email+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款地址:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+pay_address+"</dd>"
                            +"<div><figure class=\"figure\"><img src=\"/qrcode.html\" class=\"figure-img img-fluid rounded\"width=\"300\"height=\"300\"alt=\"Trinity QRcode \">"
                            +"<figcaption class=\"figure-caption text-right\">"
                            +"<h4>QRcode僅供Trinity錢包使用!</h4>"
                            +"</figcaption></figure></div>")

                flash(message)
                print "Index:",index,"Address:",pay_address,"Name:", name, " ", "Email:", email, " "
                index = index + 1

            elif check == False :
                message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"此信箱已經報名過了 !"+"</dt>")
                flash(message)
            
        else:
            message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"請確實填寫所有表格 !"+"</dt>")
            flash(message)
 
    return render_template('index.html', form=form)

@app.route("/qrcode.html")
def GenQRcode():
    return open( './static/trinity.jpg','rb').read()
    return render_template('qrcode.html')

@app.route("/reattach.html",methods=['GET', 'POST'])
def reattach():
    form = reattch_form(request.form)
    print form.errors

    if request.method == 'POST':
        txhash = request.form['txhash']

        if form.validate():

            Status = reattach(txhash)

            message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"TxHash"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+txhash+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"reattach 狀況:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+Status+"</dd>")

            flash(message)

        else:
            message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"請確實填寫所有表格 !"+"</dt>")
            flash(message)
            

    return render_template('reattach.html',form=form)

@app.route("/status.html",methods=['GET', 'POST'])
def status():
    form = check_status_form(request.form)
    print form.errors

    if request.method == 'POST':
        regemail = request.form['regemail']

        if form.validate():
            firebase_data = iota_db.get(config.iota_firebase_field,None)
            result = check_tx_status(regemail,firebase_data)
                
            if result[0]=="NO":
                message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款情況:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+"尚未付款"+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"姓名:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[1]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"信箱:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[2]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款地址"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[3]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"註冊時間"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[4]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"交易詳情"+"</dt>"
                            +"<a class="+"\""+"col-sm-9"+"\""+" href="+"\""+"https://thetangle.org/address/"+result[3]+"\""+">"+"https://thetangle.org/address/"+result[3]+"</dd>"
                    )

            elif result[0]=="YES":
                message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款情況:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+"付款成功"+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"姓名:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[1]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"信箱:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[2]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款地址"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[3]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"註冊時間"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[4]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"交易詳情"+"</dt>"
                            +"<a class="+"\""+"col-sm-9"+"\""+" href="+"\""+"https://thetangle.org/address/"+result[3]+"\""+">"+"https://thetangle.org/address/"+result[3]+"</dd>"
                    )
            
            elif result[0]=="NOTFOUND":
                message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"此信箱尚無註冊資料 !"+"</dt>")
            flash(message)

        else:
            message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"請確實填寫所有表格 !"+"</dt>")
            flash(message)

    return render_template('status.html',form=form)

@app.route("/ethindex.html",methods=['GET', 'POST'])
def ethpayment():
    form = eth_registration_form(request.form)
    print form.errors

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        eth_address = request.form['eth_address']

        if form.validate():

            firebase_data = eth_db.get(config.eth_firebase_field,None)
            check = check_email_used(email,firebase_data)
            if check == True :
                index = check_tx_index(firebase_data)
                push_to_firebase(index,timestamp(),eth_address,name.encode('utf-8'),email.encode('utf-8'),"ETH")
                message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"報名成功 !"+"</dt>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"姓名:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+name+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"信箱:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+email+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款地址:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+eth_address+"</dd>")

                flash(message)
                print "Index:",index,"Address:",eth_address,"Name:", name, " ", "Email:", email, " "
                index = index + 1

            elif check == False :
                message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"此信箱已經報名過了 !"+"</dt>")
                flash(message)
            
        else:
            message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"請確實填寫所有表格 !"+"</dt>")
            flash(message)

    return render_template('ethindex.html', form=form)

@app.route("/ethstatus.html",methods=['GET','POST'])
def eth_status():
    form = eth_check_status_form(request.form)
    print form.errors

    if request.method == 'POST':
        regemail = request.form['regemail']

        if form.validate():
            firebase_data = eth_db.get(config.eth_firebase_field,None)
            result = check_tx_status(regemail,firebase_data)
                
            if result[0]=="NO":
                message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款情況:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+"尚未付款"+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"姓名:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[1]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"信箱:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[2]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款地址"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[3]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"註冊時間"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[4]+"</dd>"
                    )

            elif result[0]=="YES":
                message = Markup("<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款情況:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+"付款成功"+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"姓名:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[1]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"信箱:"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[2]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"付款地址"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[3]+"</dd>"
                            +"<dt class="+"\""+"col-sm-3"+"\""+">"+u"註冊時間"+"</dt>"
                            +"<dd class="+"\""+"col-sm-9"+"\""+">"+result[4]+"</dd>"
                    )
            
            elif result[0]=="NOTFOUND":
                message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"此信箱尚無註冊資料 !"+"</dt>")
            flash(message)

        else:
            message = Markup("<dt class="+"\""+"text-danger"+"\""+">"+u"請確實填寫所有表格 !"+"</dt>")
            flash(message)

    return render_template('ethstatus.html',form=form)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
