from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Removes a registered Account from the System
"""
def run(args):
    res = args["api"].res
    api = args["api"]
        
    if not api.auth.guard(res, "auth/remove"):
        return
    
    if not api.requireArgs("address"):
        return
    
    
    payload = args["payload"]
    testauth = Auth(payload["address"], False)
    if not testauth.exists():
        res.set("error", "Address not existent")
        res.code(400)
        return
        
    mongo = Mongo("auth")    
        
    col = mongo.getCollection()
    delres = col.delete_one({"address": payload["address"]})
    if delres.deleted_count == 1:
        res.code(200)
    else:
        res.log("Could not delete Authentication")
        res.code(500)