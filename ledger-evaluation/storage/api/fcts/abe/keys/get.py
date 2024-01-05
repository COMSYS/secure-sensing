from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns all keys that are intermediately stored for attributes to the requester and deletes them from the database
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "authenticated"):
        return
    
    mongo = Mongo("abekeys")
    col = mongo.getCollection()
    doc = col.find_one({"address": api.auth.address})
    if doc == None:
        res.log("No key information stored")
        res.code(404)
        return
    
    keys = doc["keys"]
    
    #success = col.update_one({"address": api.auth.address}, {"$set": {"keys": {}}})
    #if success.modified_count != 1:
    #    res.code(500)
    #    return
    
    res.set("keys", keys)
    res.set("gid", api.auth.address)
    res.code(200)
    
    