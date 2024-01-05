import re
from db.Mongo import Mongo as Mongo

def run(args):
    res = args["api"].res
        
    patterns = ["*", "*/*", "*/*/*", "auth/*", "auth/register", "auth/permissions/*", "auth/*/*"]
    perms = ["auth/register", "auth/permissions/add"]
    
    for p in perms:
        for pat in patterns:
            cmp = re.compile(pat.replace("*", "\w+"))
            if cmp.fullmatch(p):
                res.log(str(p) + " matches " + str(pat))
            else:
                res.log(str(p) + " does not match " + str(pat))
    
    res.code(200)