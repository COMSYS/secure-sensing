import ujson
import sys
import json
from bson import ObjectId



class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class ApiResult:
    def __init__(self, config = {}):
        self.debug = True
        if "debug" in config:
            self.debug = config["debug"]
    
        self.dict = {
            "code": 500,
            "log": []
        }
        
    def set(self, key, val):
        self.dict[str(key)] = val
        
    def code(self, c):
        self.dict["code"] = c
        
    def send(self, c = False):
        if c != False:            
            self.dict["code"] = int(c)
            
        ret = JSONEncoder().encode(self.dict)
        return ret
        
    def log(self, str):
        self.dict["log"].append(str)
        