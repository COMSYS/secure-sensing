from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns a list of attributes and existent keys managed by the calling authority for pending key provisions or for a given account
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    payload = args["payload"]
    
    if not api.auth.guard(res, "authenticated"):
        return
           
    mongo = Mongo("abeauthorities")        
    mongo2 = Mongo("abekeys")
    
    col = mongo.getCollection()
    col2 = mongo2.getCollection()
    
    authority = col.find_one({"address": api.auth.address})
    if authority == None:
        res.code(500)
        return
    
    attributes = authority["attributes"]
    accounts = []
        
    if api.hasArgs("address"):
        force = True
        docs = col2.find({"address": payload["address"]})
        for doc in docs:
            accounts.append(doc)
    else:
        force = False
        docs = col2.find({"missingkeys": { "$exists": True, "$ne": [] }})
        for doc in docs:
            accounts.append(doc)
        
    mongo = Mongo("auth")
    col = mongo.getCollection()
    keyinfo = {}
    for acc in accounts:
        accinfo = {}
        account = col.find_one({"address": acc["address"]})
        keys = acc["keys"]
        if account == None:
            continue
        accattr = account["attributes"]
        relevantattr = []
        acckeys = []
        for a in accattr:
            if a in attributes:
                if a in acc["missingkeys"]:
                    relevantattr.append(a)
                
        if len(relevantattr) > 0 or force:
            accinfo = {
                "address": acc["address"],
                "missingkeys": relevantattr,
                "pubkey": account["pubkey"],
                "gid": account["_id"],
                "keys": acc["keys"]
            }
            keyinfo[acc["address"]] = accinfo
        

    res.set("keyinfo", keyinfo)
    res.code(200)