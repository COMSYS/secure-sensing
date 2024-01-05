from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Adds the given permissions for the given address to the existing ones
"""
def run(args):
    res = args["api"].res
    api = args["api"]
        
    if not api.auth.guard(res, "auth/permissions/add"):
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
    
    currentPerms = account.getPermissions()
    newPerms = currentPerms.copy()
    for p in permissions:
        if not p in currentPerms:
            newPerms.append(p)
    
    mongo = Mongo("auth")        
    col = mongo.getCollection()
    success = col.update_one({"address": address}, {"$set": {"permissions": newPerms}})
    if success.modified_count > 0:
        res.code(200)
    else:
        res.code(500)