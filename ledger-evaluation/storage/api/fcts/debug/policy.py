from db.Mongo import Mongo as Mongo
from auth import Auth
from accesscontrol import AccessControl

"""
Returns all registered ABE authorities as well as their API base endpoint
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    data = args["payload"]
            
    if not api.auth.guard(res, "authenticated"):
        return
    
    if not api.requireArgs("policy"):
        return
        
    p = data["policy"]
    r = api.auth.policy(p)
        
    res.set("result", r)
    res.send(200)