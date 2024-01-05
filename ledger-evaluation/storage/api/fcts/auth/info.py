from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns information about the current account or the specified one (if any)
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    
    if api.hasArgs("address"):
        if not api.auth.guard(res, "auth/info"):
            return
            
        payload = args["payload"]    
        account = Auth(payload["address"])
        if not account.exists():
            res.code(400)
            res.log("Invalid Account")
            return
        res.set("info", api.auth.getInfo())
        res.code(200)
    else:
        # Own Address
        if not api.auth.guard(res, "authenticated"):
            return
        
        res.set("info", api.auth.getInfo())
        res.code(200)