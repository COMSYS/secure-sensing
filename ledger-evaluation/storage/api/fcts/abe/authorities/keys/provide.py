from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Provides the keys for certain attributes to the given account
Keys are only stored if they match the account's attributes
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    payload = api.getArgs()
    
    if not api.auth.guard(res, "authenticated"):
        return
        
    if not api.requireArgs("address", "keys"):
        return
           
    mongo = Mongo("abeauthorities")        
    mongo2 = Mongo("abekeys")
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        return
    account = account.getAcc()
   
    
    col = mongo.getCollection()
    col2 = mongo2.getCollection()
    
    authority = col.find_one({"address": api.auth.address})
    if authority == None:
        res.log("The given authority does not exist")
        res.code(500)
        return
        
    keyaccount = col2.find_one({"address": account["address"]})
    if not keyaccount:
        res.log("The given account has no key information")
        res.code(400)        
        return
    
    attributes = authority["attributes"]
    uattributes = account["attributes"]
    missingkeys = keyaccount["missingkeys"]
    
    
    
    # Keys: Assignment of attributes to a private key encrypted with the recipients public key
    keys = payload["keys"]
    if not isinstance(keys, dict):
        res.code(400)
        return
        
    ukeys = {}
    for attr in keys:
        if attr in attributes:
            if attr in uattributes:
                if attr in missingkeys:
                    # Can be added
                    ukeys[attr] = keys[attr]
                else:
                    res.log("Key for Attribute " + attr + " is not marked as missing and won't be added")
            else:
                res.log("Attribute " + attr + " is not valid for the given account")
        else:
            res.log("Attribute " + attr + " is not valid for this authority")
            res.code(400)
            return
    
    if len(ukeys) > 0:
        nkeys = keyaccount["keys"]
        nkeys.update(ukeys)
        for nkey in ukeys:
            missingkeys.remove(nkey)
            
        updated = col2.update_one({"address": account["address"]}, {"$set": {
            "missingkeys": missingkeys,
            "keys": nkeys
        }})
        
        if updated.modified_count == 1:
            res.code(200)
        else:
            res.code(500)
    else:
        res.log("No keys to be added")
        res.code(400)