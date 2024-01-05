from db.Mongo import Mongo as Mongo
from auth import Auth
import time

"""
Creates a new Dataset
"""
def run(args):
    res = args["api"].res
    api = args["api"]
        
    if not api.auth.guard(res, "data/sc/push"):
        return

    if not api.requireArgs("data", "metadata", "signature"):
        return
    
        
    data = args["data"]
    payload = data["payload"]
    
    metadata = payload["metadata"]
    signature = data["signature"]
    
    obj = {
        "by": api.auth.getAddress(),
        "data": data,
        "time": time.time(),
        "metadata": metadata,
        "signature": signature
    }
    
    mongo = Mongo("data")          
    col = mongo.getCollection()
    id = str(col.insert_one(obj).inserted_id)
    res.set("dataid", id)
    res.send(200)