import os,base64
import time
from flask import *
from web3 import Web3
from eth_account.messages import encode_defunct
from web3.exceptions import TransactionNotFound
app=Flask(__name__)
app.secret_key = base64.urlsafe_b64encode(os.urandom(128)).decode()
BURN_ADDRESS="0x8a5aae041b46a98fac1508b24a298d08dd6e07b1"

def get_web3_proxy():
    web3=getattr(g,"_web3",None)
    if web3 is None:
        web3 = g._web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
    return web3

def get_contract():
    contract=getattr(g,"_contract",None)
    if contract is None:
        w3=get_web3_proxy()
        addr=w3.to_checksum_address("0x0909fa6D16Aaf7fea0A9A357d505E632381EFb6b")
        with open("static/abi.json","r")as fd:
            abi=json.load(fd)
        contract = w3.eth.contract(address=addr, abi=abi)
    return contract
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
    w3=get_web3_proxy()
    for i in range(12):
        try:
            data=w3.eth.get_transaction_receipt(txid)
        except TransactionNotFound:
            time.sleep(10)
        else:break
    else:
        return make_response("The transaction cannot be verified.",500)
    if data["from"].lower()!=session["address"]:
        return make_response("txId invaild.",400)
    contract=get_contract()
    args=contract.events.Transfer().process_receipt(data)[0]["args"]
    print(args)
    amount=args["value"]
    # TODO:余额转入论坛
    # _mint_NL(username,amount)
    return "%d NL has been withdrawn to %s"%(amount,username)

@app.route("/")
def inedex():
    return render_template("index.html",dst=BURN_ADDRESS)
