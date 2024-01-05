from db.Mongo import Mongo as Mongo
from auth import Auth


"""
Returns a list of Attributes for the given address
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    
    if not api.requireArgs("address"):
        return
        
    if not api.auth.guard(res, "auth/attributes/get"):
        return
    
    payload = args["payload"]
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        res.log("Invalid Account")
        return
        
    res.set("attributes", account.getAttributes())
    res.code(200)