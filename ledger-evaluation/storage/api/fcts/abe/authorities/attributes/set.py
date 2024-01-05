from db.Mongo import Mongo as Mongo
from auth import Auth
import sys
import config
sys.path.insert(0,config.parentdir)
import gclasses.gconfig as gconfig

"""
Sets the Attributes (overwrites them) managed by the given Authority
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "authenticated"):
        return
        
    if not api.requireArgs("address", "attributes", "pk"):
        return
        
    payload = args["payload"]
    address = payload["address"]
    pk = payload["pk"]
    
    delm = gconfig.attribute_delimiter
    
    if not api.auth.guard(res, "is/" + address):
        return
        
    if not isinstance(payload["attributes"], list):
        res.code(400)
        res.log("attributes have to be passed as array")
        return
        
    
        
    mongo = Mongo("abeauthorities")        
    col = mongo.getCollection()    
    authority = col.find_one({"address": payload["address"]})
    if authority == None:
        res.set("error", "Authority not found")
        res.code(404)
        return        
        
    attributes = payload["attributes"]
    # Verify postfix
    postfix = authority["postfix"]
    attributes = list(map(lambda x: x.upper(), attributes))
    
    for attr in attributes:
        name = attr.split(delm)
        if len(name) != 2:
            res.set("error", "Attribute " + attr + " does not follow attribute name guideline")
            res.code(400)
            return
        elif delm + name[1] != postfix:
            res.set("error", "Attribute " + attr + " has invalid postfix. Required: " + postfix + " - Got: " + name[1])
            res.code(400)
            return
            
    
    success = col.update_one({"address": address}, {"$set": {"attributes": attributes, "pk": pk}})
    if success.modified_count > 0:
        res.code(200)
    else:
        res.code(500)