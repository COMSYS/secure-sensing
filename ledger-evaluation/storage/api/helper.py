from db.Mongo import Mongo as Mongo
from bson.objectid import ObjectId

def verifyRecordAccess(args):
    res = args["api"].res
    api = args["api"]    
    data = args["payload"]

    if not api.auth.guard(res, "authenticated"):
        return 
    
    if not api.requireArgs("_id"):
        return False
        
    id = ObjectId(data["_id"])
    mongo = Mongo("data")
    col = mongo.getCollection()
    doc = col.find_one({"_id": id})
    
    if doc == None:
        res.code(404)
        res.log("Invalid ID")
        return False
        
    policy = None
    if "_policy" in doc:
        policy = doc["_policy"]
    fp = False
    if "_forcepolicy" in doc:
        fp = doc["_forcepolicy"]
        
    if policy != None:
        if fp:
            res.code(500)
            res.log("Policy Enforcement not implemented yet")
            return False
        if not api.auth.policy(res, policy):
            return False
            
    return {
        "doc": doc,
        "col": col,
        "id": id
    }
    
def verifyRecordsAccesses(args):
    res = args["api"].res
    api = args["api"]    
    data = args["payload"]

    if not api.auth.guard(res, "authenticated"):
        return 
    
    if not api.requireArgs("_ids"):
        return False
        
    
    
    mongo = Mongo("data")
    col = mongo.getCollection()
    
    ids = data["_ids"]
    
    ors = []
    
    for strid in ids:    
        ors.append({"_id": ObjectId(strid)})
        
    
    docs = col.find({"$or": ors})
    if docs.count() == 0:
        res.code(404)
        res.log("Invalid IDs")
        return False
    
    rdocs = {}
    
    for doc in docs: 
        oid = str(doc["_id"])
        rdocs[oid] = False
        policy = None
        if "_policy" in doc:
            policy = doc["_policy"]
        fp = False
        if "_forcepolicy" in doc:
            fp = doc["_forcepolicy"]
            
        if policy != None:
            if fp:
                #res.code(500)
                res.log("Policy Enforcement not implemented yet")
                continue
            if not api.auth.policy(res, policy):
                res.log("Policy not satisfied")
                continue
        rdocs[oid] = doc
            
    return {
        "docs": rdocs,
        "col": col
    }