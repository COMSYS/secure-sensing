from db.Mongo import Mongo as Mongo
from auth import Auth
from versioning import Versioning
from bson.objectid import ObjectId
import helper


"""
Produce and Trade Information for multiple IDs.
"""
def run(args):
    res = args["api"].res
    api = args["api"]    
    data = args["payload"]
        
        
    docsinfo = helper.verifyRecordsAccesses(args)
    
    if not docsinfo:
        return
        
    docs = docsinfo["docs"]    
    col = docsinfo["col"]
            
    v = Versioning()
    reqv = False
    if api.hasArgs("version"):
        reqv = int(data["version"])
    
    vdocs = {}
    
    for id in docs:        
        doc = docs[id]
        if doc != False:
            versioned = v.getRecord(doc, reqv)
            vdocs[id] = versioned
        else:
            vdocs[id] = False
    
    res.set("data", vdocs)    
    res.code(200)