from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns the encoded global parameters from ABE setup to be used for bootstrapping after updating the associated record to the given value
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "abe/config/set"):
        return
        
    if not api.requireArgs("gp"):
        return
        
    mongo = Mongo("abeconf")
        
    conf = {
        "type": "global_params",
        "gp": payload["gp"]
    }
        
    col = mongo.getCollection()    
    result = col.replace_one({"type": "global_params"}, conf, True)
    
    if result.modified_count == 0 and result.upserted_id == None:
        # Upsert failed
        res.error("Upsert failed")
        res.code(500)
    else:
        res.set("global_params", payload["gp"])
        res.code(200)