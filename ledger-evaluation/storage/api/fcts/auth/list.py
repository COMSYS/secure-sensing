from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Lists all registered accounts / authentications
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "auth/list"):
        return
    
    
    mongo = Mongo("auth")
        
    col = mongo.getCollection()
    auths = []
    for c in col.find():
        auths.append(c)
    res.set("auths", auths)
    res.code(200)