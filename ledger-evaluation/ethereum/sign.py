import ujson
import hashlib
import hmac
import time
from eth_account import Account
from eth_account.messages import encode_defunct
from web3.auto import w3

def sign(account, data):
    key = account["privateKey"]
    intkey = int(key, 16)
    
    if "privateKeyObject" in account:
        intkey = account["privateKeyObject"]
    json = ujson.dumps(data["data"])
    msghash = encode_defunct(text=json)
    signature = Account.sign_message(msghash, intkey)
    data["signature"] = {
        "messageHash": signature["messageHash"].hex(),
        "signature": signature["signature"].hex(),
        "r": hex(signature["r"]),
        "s": hex(signature["s"]),
        "v": hex(signature["v"])
    }
        
    return data
    
def signStr(account, msg):
    key = account["privateKey"]
    intkey = int(key, 16)   
    if "privateKeyObject" in account:
        intkey = account["privateKeyObject"] 
    #s = time.time()
    msghash = encode_defunct(text=msg)
    #print("signStr Hash: " + str(time.time()-s))
    
    #s = time.time()
    signature = Account.sign_message(msghash, intkey)        
    #print("signStr Sig: " + str(time.time()-s))
    sig = {
        "messageHash": signature["messageHash"].hex(),
        "signature": signature["signature"].hex(),
        "r": hex(signature["r"]),
        "s": hex(signature["s"]),
        "v": hex(signature["v"])
    }
    return sig
    
def validateSignatureStr(msg, signature, signer):
    msghash = encode_defunct(text=msg)
    
    vrs = (signature["v"], signature["r"], signature["s"])
    
    address = Account.recover_message(msghash, vrs=vrs)
    #address = w3.eth.account.recover_message(msghash, vrs=vrs)
    if (address == signer):        
        return True
    
    return False