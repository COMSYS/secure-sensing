from eth_account import Account
from eth_keys import keys
from eth_utils import decode_hex
from eth_utils.curried import keccak
import sys
import ujson

def main(seed):
    if seed == None:
        acct = Account.create(seed);
    else:
        key_bytes = keccak(seed.encode())
        acct = Account.from_key(key_bytes)
        
    pkey = keys.PrivateKey(acct.key)
    pubkey = pkey.public_key
    info = {
        "privateKey": acct.key.hex(),
        "address": acct.address,
        "publicKey": pubkey.to_hex(),
        "sk": False
    }
    print(ujson.dumps(info))    
    
if __name__ == "__main__":
    seed = None
    if len(sys.argv) > 1:
        seed = sys.argv[1]
    main(seed)