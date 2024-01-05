import pymongo
import ujson

"""
A wrapper for the MongoDb connection
"""

dbpool = None

class Mongo:
    def __init__(self, collection = False):
        global dbpool
        self.config = False
        self.loadConfig()       
        
        if not self.config["address"] in dbpool:
            print("Opening MongoDB Connection")
            dbpool[self.config["address"]] = pymongo.MongoClient(self.config["address"])
            
        self.client = dbpool[self.config["address"]]
        self.db = self.client[self.config["database"]]
        self.collection = None
        if collection != False:
            if collection in self.config:
                self.collection = self.db[self.config[collection]]
            elif collection + "collection" in self.config:
                self.collection = self.db[self.config[collection+"collection"]]
        
    def dropDb(self):
        if self.client == None:
            return False
            
        self.client.drop_database(self.config["database"])
        return True
        
    def selectDb(self, database):
        self.db = self.client[database]
        return self.db
        
    def listDb(self):
        return self.client.list_database_names()
        
    def listCollections(self):
        if self.db == None:
            return []
        return self.db.list_collection_names()
        
    def selectCollection(self, collection):
        if self.db == None:
            return False
        self.collection = self.db[collection]
        return self.collection
        
    def getCollection(self):
        return self.collection
        
    """
    Inserts the given dict into the currently selected Collection.
    Returns the ID of the inserted Document.
    """
    def insertOne(self, dict):
        if self.collection == None:
            return False
        x = self.collection.insert_one(dict)       
        return x.inserted_id
        
    """
    Inserts the given array of dicts into the currently selected Collection.
    Returns the IDs of the inserted Documents.
    """    
    def insertMany(self, dicts):
        if self.collection == None:
            return False
        x = self.collection.insert_many(dicts)
        return x.inserted_ids
        
        
    
    def findOne(self, query = None):        
        if self.collection == None:
            return False
        return self.collection.find_one(query)
        
    def findAll(self, query = None):        
        if self.collection == None:
            return False
        return self.collection.find()
        
    def loadConfig(self):
        try:
            with open("../config/database.conf", 'r') as file:
                self.config = ujson.loads(file.read())
            return True
        except Exception as e:
            print(repr(e))
            return False
            
    def getConf(self, key = False):
        if not key:
            return self.config
        
        if key in self.config:
            return self.config[key]
        
        return None
    