from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns all registered ABE authorities as well as their API base endpoint
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    data = args["data"]
            
    if not api.auth.guard(res, "authenticated"):
        return
    
    ndata = {}
    if "payload" in data:
        ndata["payload"] = data["payload"]
    if "__encryptinfo" in data:
        ndata["__encryptinfo"] = data["__encryptinfo"]
        
    res.set("data", ndata)
    #res.set("request_args", False)
    res.send(200)