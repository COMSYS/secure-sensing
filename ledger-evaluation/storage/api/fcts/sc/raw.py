from db.Mongo import Mongo as Mongo
from auth import Auth
from versioning import Versioning
from bson.objectid import ObjectId
import helper


"""
Produce and Trade Information.
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    data = args["payload"]
        
        
    docinfo = helper.verifyRecordAccess(args)
    
    if not docinfo:
        return

    res.set("data", docinfo["doc"])
    res.code(200)
