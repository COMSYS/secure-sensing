import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from api import Api

# Process persitent MongoDB Pool. Avoid closing / opening connections
dbpool = {}

"""
This is called by the Apache Webserver via the WSGI Module
"""
def application(env, startResponse):
    global dbpool
    import db.Mongo
    db.Mongo.dbpool = dbpool
    
    startResponse("200 OK", [("Content-type", "application/json")])
    
    api = Api()
    
    path = list(filter(None, env["PATH_INFO"].split("/")))
    
    args = {
        "env": env,
        "path": path
    }
    
    #ret = (str(sys.path) + str(sys.prefix) + " --- " + str(sys.version)).encode()
    
    ret = api.handle(args)
    
    return [str(ret).encode()]
    
    
    #return [ret]
