import os,base64
import time

import sqlite3,json
from flask import *
from eth_account.messages import encode_defunct
from web3.exceptions import TransactionNotFound
from utils import init_db,_get_web3_proxy,_get_contract,_get_database_connect
init_db()
app=Flask(__name__)
app.secret_key = base64.urlsafe_b64encode(os.urandom(128)).decode()
BURN_ADDRESS="0x8a5aae041b46a98fac1508b24a298d08dd6e07b1" #不是什么销毁地址，这是我的钱包（）

def get_web3_proxy():
    web3=getattr(g,"_web3",None)
    if web3 is None:
        web3 = g._web3 = _get_web3_proxy()
    return web3

def get_contract():
    contract=getattr(g,"_contract",None)
    if contract is None:
        contract=g._contract=_get_contract()
    return contract

def get_database_connect():
    conn=getattr(g,"_db",None)
    if conn is None:
        conn=g._db=_get_database_connect()
    return conn

@app.route("/challenge/<addr>")
def get_challenge(addr:str):
    s="nl-challenge-"+base64.urlsafe_b64encode(os.urandom(48)).decode()
    session["challenge"]=(addr.lower(),s)
    return jsonify({"s":s})

@app.route("/verify",methods=["POST"])
def check_challenge():
    if not request.is_json:
        return make_response("Request invaild.",400)
    addr,challenge=session["challenge"]
    sig=request.json["sig"]
    web3=get_web3_proxy()
    sig_addr=web3.eth.account.recover_message(encode_defunct(text=challenge),signature=sig).lower()
    if sig_addr==addr:
        del session["challenge"]
        session["address"]=sig_addr
        return "OK"
    else:
        return make_response("Signature invaild.",403)

@app.route("/withdraw",methods=["POST"])
def withdraw():
    if not request.is_json\
        or "id" not in request.json\
            or "username" not in request.json:
        return make_response("Request invaild.",400)
    txid=request.json["id"]
    username=request.json["username"]
    
    db=get_database_connect()
    cur=db.cursor()
    res=cur.execute("select id,username from record where txid = ?",(txid,)).fetchall()
    cur.close()
    if len(res):
        #print(res)
        num,user=res[0]
        return make_response("txId has been used by %s in #%d transaction."%(user,num),400)

    w3=get_web3_proxy()
    for i in range(12):
        try:
            data=w3.eth.get_transaction(txid)
        except TransactionNotFound:
            time.sleep(10)
        else:break
    else:
        return make_response("The transaction cannot be verified.",500)
    if data["from"].lower()!=session.get("address"):
        return make_response("address invaild.",400)
    contract=get_contract()
    _,data=contract.decode_function_input(data["input"])
    amount=data.get("value",-1)/(10**int(contract.functions.decimals.call()))

    if data["to"].lower()!=BURN_ADDRESS.lower():
        return make_response("The transaction cannot be verified.",500)
    cur=db.cursor()
    cur.execute("insert into record (txid,username) values (?,?)",(txid,username))
    cur.close()
    db.commit()
    # TODO:余额转入论坛
    # _mint_NL(username,amount)
    return "%d NL has been withdrawn to %s"%(amount,username)

@app.route("/")
def inedex():
    return render_template("index.html",dst=BURN_ADDRESS)
