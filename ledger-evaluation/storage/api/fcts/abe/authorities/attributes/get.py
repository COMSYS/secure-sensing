from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns the Attributes managed by the given Authority
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "authenticated"):
        return
        
    if not api.requireArgs("address"):
        return
        
    payload = args["payload"]
    
    if not api.auth.guard(res, "is/" + payload["address"]):
        return
        
    mongo = Mongo("abeauthorities")        
    col = mongo.getCollection()
    
    authoritiy = col.find_one({"address": payload["address"]})
    if authoritiy == None:
        res.set("error", "Authority not found")
        res.code(404)
    else:
        res.set("attributes", authoritiy["attributes"])
        res.code(200)