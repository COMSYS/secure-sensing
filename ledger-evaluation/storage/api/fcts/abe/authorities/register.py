from db.Mongo import Mongo as Mongo
from auth import Auth
import sys
import config
sys.path.insert(0, config.parentdir)
import gclasses.gconfig as gconfig
import time

"""
Registers a new CTABE-Authority
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "authenticated"):
        return
        
    if not api.requireArgs("name", "address", "pubkey"):
        return
        
    payload = args["payload"]
    
    if not api.auth.guard(res, "is/" + payload["address"]):
        return
        
    mongo = Mongo("abeauthorities")        
    col = mongo.getCollection()
    
    obj = {
        "name": payload["name"],
        "registered": time.time(),
        "attributes": [],
        "address": payload["address"],
        "pubkey": payload["pubkey"]
    }
    
    ido = col.insert_one(obj).inserted_id
    id = str(ido)
    
    if id == None or id == "":
        res.set("error", "Could not register authority")
        res.code(500)
        return
    
    delm = gconfig.attribute_delimiter
    postfix = delm + id
    postfix = postfix.upper()
    
    result = col.update_one({"_id": ido}, {"$set": {"postfix": postfix}})
    res.set("authority_postfix", postfix)
    res.set("authority_id", id)
    res.code(200)