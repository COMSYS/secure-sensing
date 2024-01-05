from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Sets the permissions (overwrites them) for the given address with the given array of permissions
"""
def run(args):
    res = args["api"].res
    api = args["api"]
        
    if not api.auth.guard(res, "auth/permissions/set"):
        return
    
    if not api.requireArgs("permissions", "address"):
        return
    
    payload = args["payload"]
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        res.log("Invalid Account")
        return
    
    if not isinstance(payload["permissions"], list):
        res.code(400)
        res.log("permissions have to be passed as array")
        return
    
    address = payload["address"]
    permissions = payload["permissions"]
    
    mongo = Mongo("auth")        
    col = mongo.getCollection()
    success = col.update_one({"address": address}, {"$set": {"permissions": permissions}})
    if success.modified_count > 0:
        res.code(200)
    else:
        res.code(500)