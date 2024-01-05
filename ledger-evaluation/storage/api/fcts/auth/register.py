from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Registers a new Account in to the System without any attributes or permissions
"""
def run(args):
    res = args["api"].res
    api = args["api"]
        
    if not api.auth.guard(res, "auth/register"):
        return
    
    if not api.requireArgs("pubkey", "address", "name"):
        return
    
    
    payload = args["payload"]
    testauth = Auth(payload["address"], False)
    if testauth.exists():
        res.set("error", "Address already registered")
        res.code(400)
        return
        
    mongo = Mongo("auth")
        
    obj = {
        "address": payload["address"],
        "name": payload["name"],
        "pubkey": payload["pubkey"],
        "active": True,
        "permissions": [],
        "attributes": []
    }
    
        
    col = mongo.getCollection()
    id = str(col.insert_one(obj).inserted_id)
    res.set("accountid", id)
    res.code(200)