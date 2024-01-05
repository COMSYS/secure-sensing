from db.Mongo import Mongo as Mongo
from auth import Auth
import config
import sys
sys.path.insert(0,config.parentdir)
from gclasses.ctabe import CtAbe

"""
Returns the encoded global parameters from ABE setup to be used for bootstrapping after performing abe setup to create new global parameters
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    
    if not api.auth.guard(res, "abe/config/set"):
        return        
        
    mongo = Mongo("abeconf")
    
    ctabe = CtAbe()
    ctabe.genGlobalParams()
    gp = ctabe.serializeGP().decode();
        
    conf = {
        "type": "global_params",
        "gp": gp
    }
        
    col = mongo.getCollection()    
    result = col.replace_one({"type": "global_params"}, conf, True)
    
    if result.modified_count == 0 and result.upserted_id == None:
        # Upsert failed
        res.error("Upsert failed")
        res.code(500)
    else:
        res.set("global_params", gp)
        res.code(200)