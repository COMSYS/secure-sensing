from db.Mongo import Mongo as Mongo

def run(args):
    res = args["api"].res
    
    mongo = Mongo("data")
    col = mongo.getCollection()
    
    docs = []
    
    for doc in col.find():
        docs.append(doc)
    
    res.set("docs", docs)
    res.code(200)
    return True
