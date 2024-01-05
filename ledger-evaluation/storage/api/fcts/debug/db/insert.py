from db.Mongo import Mongo as Mongo

def run(args):
    res = args["api"].res
    payload = {}
    if "payload" in args:
        payload = args["payload"]

    dict = args["databaseconfig"]
    res.log(str(dict))
    mongo = Mongo(dict)
    mongo.selectDb("test")
    
    obj = {}
    
    for key, val in payload.items():
        obj[key] = val
    
    if len(obj) == 0:
        obj["default_key"] = "default_value"
    
    col = mongo.selectCollection("test")
    id = str(col.insert_one(obj).inserted_id)
    res.log("Inserted " + str(obj) +  " with ID " + id)
    
    res.log("Listing all Records")
    for doc in mongo.findAll():
        res.log("  " + str(doc))
    res.code(200)