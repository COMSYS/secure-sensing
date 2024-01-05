from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Set the given attributes for the given address (Overwrites existing ones)
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    
    if not api.requireArgs("attributes", "address"):
        return
        
    if not api.auth.guard(res, "auth/attributes/set"):
        return
    
    payload = args["payload"]
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        res.log("Invalid Account")
        return
    
    if not isinstance(payload["attributes"], list):
        res.code(400)
        res.log("attributes have to be passed as array")
        return
    
    address = payload["address"]
    attributes = payload["attributes"]
   
    mongo = Mongo("auth")        
    col = mongo.getCollection()
    success = col.update_one({"address": address}, {"$set": {"attributes": attributes}})
    if success.modified_count > 0:
        res.code(200)
    else:
        res.code(500)