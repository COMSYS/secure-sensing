from db.Mongo import Mongo as Mongo
from auth import Auth
import time

"""
Transport registering. See "Transaction Format: Transport" section of docs/datascheme.md
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    
    data = args["payload"]
    
    if not api.auth.guard(res, "authenticated"):
        return 
    
    if not api.requireArgs("_reference", "_recipient"):
        return
        
    reference = data["_reference"]
    recipient = data["_recipient"]
    
    # Batch Size
    if api.hasArgs("_batch"):
        batch = data["_batch"]
    else:
        batch = {
            "size": 1
        }
    if not isinstance(batch, dict):
        res.code(400)
        res.log("Invalid Batch")
        return
    
    # Policy and Enforcement
    forcepolicy = False
    if api.hasArgs("_forcepolicy"):
        forcepolicy = data["_forcepolicy"]
    if not isinstance(forcepolicy, bool):
        res.code(400)
        res.log("Invalid forcepolicy value")
        return
        
    policy = None
    if api.hasArgs("_policy"):
        policy = data["_policy"]
        if not isinstance(policy, str):
            res.code(400)
            res.log("Invalid Policy: Must be string")
            return
            
    einfo = None
    if api.hasArgs("__encryptinfo"):
        einfo = data["__encryptinfo"]
        if not isinstance(einfo, dict) or not "keys" in einfo or not "pubkey" in einfo:
            res.code(400)
            res.log("Invalid Encryption Info")
            return
        
    tracking = {}
    if api.hasArgs("_tracking"):
        tracking = data["_tracking"]
        if not isinstance(tracking, dict):
            res.code(400)
            res.log("Invalid Tracking information")
            return
            
    
    insert = {
        "_sender": api.auth.address,
        "_recipient": recipient,
        "_reference": reference,
        "_tracking": tracking,
        "_batch": batch,
        "__version": 1,
        "__versioninfo": {
            "__v1": {
                "timestamp": time.time(),
                "actor": api.auth.address
            }
        },
        "_type": "trade"
    }
    
    if einfo != None:
        insert["__encryptinfo"] = einfo
    if policy != None:
        insert["_policy"] = policy
    if forcepolicy:
        insert["_forcepolicy"] = True
    
    mongo = Mongo("data")
    col = mongo.getCollection()
    id = col.insert_one(insert).inserted_id
    insert["_id"] = id
    
    res.set("data", insert)    
    res.code(200)