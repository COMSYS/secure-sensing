from db.Mongo import Mongo as Mongo

def run(args):
    res = args["api"].res

    mongo = Mongo("data")
    col = mongo.getCollection()
    x = col.delete_many({})
    res.log("Deleted " + str(x.deleted_count) + " documents")
    res.code(200)
    return True