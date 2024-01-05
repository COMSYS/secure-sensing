import ujson
from db.Mongo import Mongo as Mongo
import re
from accesscontrol import AccessControl

class Auth:
    def __init__(self, address = False, validSig = False, config = False):
        self.address = address
        self.validSig = validSig
        self.mongo = Mongo("auth")
        self.acc = False
        self.config = config
       
    def getAcc(self):
        if not self.acc == False:
            return self.acc
        
        c = self.mongo.getCollection()
        acc = c.find_one({"address": self.address})
        if acc == None:
            return False
        
        self.acc = acc
        return acc
        
    def getInfo(self):
        return repr(self.getAcc())
       
    """
    Checks whether the current account is valid and authentication was successful
    """
    def isValid(self):
        acc = self.getAcc()
        if not acc:
            return False
        return self.validSig and acc["active"]
       
    """
    Checks whether an account with the current address exists
    """
    def exists(self):
        acc = self.getAcc()
        if not acc:
            return False
        return True
        
    """
    Checks if the currently authenticated account has a certain permission
    """    
    def hasPerm(self, permission):
        # Allows the admin to create arbitrary accounts (at system setup)
        if self.config != False and self.config["permission-override"] == True:
            return True

        if not self.address:
            return False
            
        if not self.isValid():
            return False
                
        acc = self.getAcc()
        if not acc:
            return False
        
        perms = acc["permissions"]
        
        perms = self._addDefaultPermissions(perms)
        
        for p in perms:
            if p == permission:
                return True
            # Try regex match
            # For /auth/* should match /auth/fcta and /auth/fctb as well as /auth/xyz/fctc
            pattern = re.compile(p.replace("*", "\w+"))            
            if pattern.fullmatch(permission):
                return True
        
        if permission in perms:
            return True
        
        return False
        
    """
    Ensures the current user has all of the given permissions
    """
    def guard(self, res, *perms):
        ret = True
        for p in perms:
            if not self.hasPerm(p):
                ret = False
                res.log("User: " + self.getInfo())
                res.log("Missing Permission: " + repr(p))
                res.code(401)
                
        return ret
        
    """
    Ensures the attributes of a user satisfy the given policy
    """
    def policy(self, res, policy):
        acc = AccessControl(self.getAcc())
        if not acc.checkPolicy(policy):            
            res.log("Policy not satisfied: " + repr(policy))
            res.code(401)
            return False
        return True
        
    """
    Returns the Account name of the current account
    """
    def getAccountName(self):
        return self._attrOrDef("name", False)
        
    def isActive(self):
        return self._attrOrDef("active", False)
        
    def getPermissions(self):
        return self._attrOrDef("permissions", [])
        
    def getAttributes(self):
        return self._attrOrDef("attributes", [])

    def getAddress(self):
        return self._attrOrDef("address", False)
        
    def _attrOrDef(self, attr, fallback):
        acc = self.getAcc()
        if not acc:
            return fallback
        if not attr in acc:
            return fallback
        return acc[attr]
        
    def _addDefaultPermissions(self, perms):
        ret = perms.copy()
        if self.isValid():
            ret.append("authenticated")
            ret.append("is/" + self.address)
            
        return ret
