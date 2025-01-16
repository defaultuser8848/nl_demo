import sqlite3
from flask import *
from web3 import Web3


def init_db():
    conn=sqlite3.connect("record.db")
    cur=conn.cursor()
    with open("init.sql","r")as f:
        cur.execute(f.read())
    cur.close()
    conn.commit()
    conn.close()

def _get_web3_proxy():
    return Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def _get_contract():
    w3=_get_web3_proxy()
    addr=w3.to_checksum_address("0x0909fa6D16Aaf7fea0A9A357d505E632381EFb6b")
    with open("static/abi.json","r")as fd:
        abi=json.load(fd)
    contract = w3.eth.contract(address=addr, abi=abi)
    return contract

def _get_database_connect():
    return sqlite3.connect("record.db")