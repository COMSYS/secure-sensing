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
        
    doc = docinfo["doc"]
    id = docinfo["id"]
    col = docinfo["col"]
            
    v = Versioning()
    reqv = False
    if api.hasArgs("version"):
        reqv = int(data["version"])
        if reqv == 0:
            reqv = False
    
    versioned = v.getRecord(doc, reqv)
    
    res.set("data", versioned)    
    res.code(200)