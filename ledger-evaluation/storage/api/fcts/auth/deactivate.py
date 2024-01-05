from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Deactivates the specified account
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "auth/deactivate"):
        return

    if not api.requireArgs("address"):
        return
    
    payload = args["payload"]
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        res.log("Invalid Account")
        return
    
    address = payload["address"]
    
    
    mongo = Mongo("auth")        
    col = mongo.getCollection()
    success = col.update_one({"address": address}, {"$set": {"active": False}})
    if success.modified_count > 0:
        res.code(200)
    else:
        res.code(500)