import ujson
import hashlib
import hmac
from eth_account import Account
from eth_account.messages import encode_defunct
import ecies

def encrypt(data, pubkey):    
    edata = ecies.encrypt(pubkey, data.encode())        
    return edata.hex()
    