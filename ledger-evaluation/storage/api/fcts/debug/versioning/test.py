from db.Mongo import Mongo as Mongo
from auth import Auth
from versioning import Versioning
import copy

"""
Returns all registered ABE authorities as well as their API base endpoint
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    data = args["data"]
    
    vt = Versioning()
    
    v1 = {
        "info": {
            "key1": {
                "key1_2": "asd"
            },
            "key2": "asd"
        },
        "__version": 1
    }
            
    v2 = copy.deepcopy(v1)
    updates = {
        "u1": {
            "path": "key1.key1_2",
            "value": {
                "now": "an object"
            }
        },
        "u2": {
            "path": "key1.key1_new",
            "value": "A new key that did not exist in v1"
        }
    }
    
    set2 = vt.updateRecord(v2, updates, "info")
    
    
    v3 = copy.deepcopy(v2)
    updates2 = {
        "u1": {
            "path": "key1.key1_2",
            "value": {
                "__deleted": True
            }
        }
    }
    
    set3 = vt.updateRecord(v3, updates2, "info")
    
    v3raw = vt.getRecord(v3, 3)
    v2raw = vt.getRecord(v3, 2)
    v1raw = vt.getRecord(v3, 1)
    
    res.set("v1", v1)
    res.set("v2", v2)
    res.set("v3", v3)
    res.set("v2raw", v2raw)
    res.set("v1raw", v1raw)
    res.set("v3raw", v3raw)
    res.set("set2", set2)
    res.set("set3", set3)
    
    res.send(200)