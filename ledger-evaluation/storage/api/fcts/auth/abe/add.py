from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Adds the given attributes for the given address to the existing ones
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    
    if not api.requireArgs("attributes", "address"):
        return
        
    if not api.auth.guard(res, "auth/attributes/add"):
        return
    
    payload = args["payload"]
    
    account = Auth(payload["address"])
    if not account.exists():
        res.code(400)
        res.log("Invalid Account")
        return
    
    if not isinstance(payload["attributes"], list):
        res.code(400)
        res.log("attributes have to be passed as array")
        return
    
    address = payload["address"]
    attributes = payload["attributes"]
    
    currentAttr = account.getAttributes()
    newAttr = currentAttr.copy()
    changed = []
    for p in attributes:
        if not p in currentAttr:
            newAttr.append(p)
            changed.append(p)
    
    mongo = Mongo("auth")        
    col = mongo.getCollection()
    success = col.update_one({"address": address}, {"$set": {"attributes": newAttr}})
    if success.modified_count > 0:
        if len(changed) > 0:
            mongo = Mongo("abekeys")
            col = mongo.getCollection()
            info = col.find_one({"address": address})
            if info == None:
                col.insert({"address": address, "keys": {}, "missingkeys": changed})
            else:
                missingkeys = info["missingkeys"] + changed
                succ = col.update_one({"address": address}, {"$set": {"missingkeys": missingkeys}})
                if succ.modified_count == 0:
                    res.code(500)
                    return
        res.code(200)
    else:
        res.code(500)