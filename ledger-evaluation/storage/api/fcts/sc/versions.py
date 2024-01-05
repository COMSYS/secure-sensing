from db.Mongo import Mongo as Mongo
from auth import Auth
from versioning import Versioning
from bson.objectid import ObjectId
import helper


"""
Produce and Trade Information (all Versions)
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
    maxversion = doc["__version"]
    
    versions = []
    
    for reqv in range(maxversion):
        versions.append(v.getRecord(doc, reqv + 1))
    
    res.set("versions", versions)
    res.code(200)