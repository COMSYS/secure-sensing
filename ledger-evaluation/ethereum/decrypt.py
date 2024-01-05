import ujson
import hashlib
import hmac
from eth_account import Account
from eth_account.messages import encode_defunct
import ecies
    
def decrypt(edata, privkey):
    ke = bytes.fromhex(edata)
    data = ecies.decrypt(privkey, ke)
    return data.decode()
    
    