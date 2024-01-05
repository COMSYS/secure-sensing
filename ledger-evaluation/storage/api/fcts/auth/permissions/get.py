from db.Mongo import Mongo as Mongo
from auth import Auth


"""
Returns a list of Permissions for the given address
"""
def run(args):
    res = args["api"].res
    api = args["api"]
        
    if not api.auth.guard(res, "auth/permissions/get"):
        return
    
    if not api.requireArgs("address"):
        return
    
    payload = args["payload"]
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        res.log("Invalid Account")
        return
        
    res.set("permissions", account.getPermissions())
    res.code(200)