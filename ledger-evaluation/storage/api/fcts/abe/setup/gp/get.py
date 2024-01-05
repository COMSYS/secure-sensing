from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns the encoded global parameters from ABE setup to be used for bootstrapping
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    if not api.auth.guard(res, "authenticated"):
        return
        
    mongo = Mongo("abeconf")
        
    col = mongo.getCollection()
    
    gp = col.find_one({"type": "global_params"})
    if gp == None:
        res.set("error", "API Setup not completed")
        res.code(500)
    else:
        res.set("global_params", gp["gp"])
        res.code(200)