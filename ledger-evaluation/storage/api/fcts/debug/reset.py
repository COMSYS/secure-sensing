from db.Mongo import Mongo as Mongo
from auth import Auth

"""
Returns all registered ABE authorities as well as their API base endpoint
"""
def run(args):
    res = args["api"].res
    api = args["api"]
            
    #if not api.auth.guard(res, "reset"):
    #    return
    
    
    mongo = Mongo()
        
    if mongo.dropDb():    
        res.code(200)
    else:
        res.code(500)