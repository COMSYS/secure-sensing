import ujson
import config
import sys
import boolean
sys.path.insert(0, config.parentdir)
import gclasses.gconfig as gconfig
import gclasses.dictutils as dictutils
from db.Mongo import Mongo as Mongo

class AccessControl:
    def __init__(self, accinfo):
        self.account = accinfo
        self.allattributes = None
        
    def getAllAttributes(self):
        if self.allattributes != None:
            return self.allattributes
            
        mongo = Mongo("abeauthorities")
        col = mongo.getCollection()
        items = col.find()
        self.allattributes = []
        
        for a in items:
            self.allattributes = self.allattributes + a["attributes"]
            
        return self.allattributes
        
    """
    Checks if the attributes of the linked account satisfy the given policy
    """
    def checkPolicy(self, policy):
        uattr = self.account["attributes"]
        aattr = self.getAllAttributes()
        repl = {}
        p = policy
        # Replace all attribute names the user has with "1", all others with "0"
        for a in aattr:
            if a in uattr:
                p = p.replace(a, "1")
            else:
                p = p.replace(a, "0")
        algebra = boolean.BooleanAlgebra()
        satisfies = algebra.parse(p, True)
        return repr(satisfies).lower() == "true"