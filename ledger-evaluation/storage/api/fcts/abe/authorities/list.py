from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns all registered ABE authorities as well as their API base endpoint
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "authenticated"):
        return
    
    
    mongo = Mongo("abeauthorities")
        
    col = mongo.getCollection()
    auths = []
    for c in col.find():
        auths.append(c)
    res.set("authorities", auths)
    res.code(200)