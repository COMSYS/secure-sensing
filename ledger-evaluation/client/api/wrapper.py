import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
rootdir = os.path.dirname(parentdir)
sys.path.insert(0,rootdir)
sys.path.insert(0,currentdir)

import requests
import api
from gclasses.fileutils import file_get_contents
import pymongo
from eth_keys import keys
from hexbytes import HexBytes
import json

instance = None

class ApiWrapper:
    def __init__(self, opts = {}):
        self.defoptions = {
            "configfile": "",
            "type": "post",
            "policy": "",
            "encrypt": [],
            "encryptprefix": "",
            "decrypt": False,
            "keepencrypted": False,
            "addscsig": True,
            "addfingerprint": True,
            "rpcprovider": None,            
            "requestbc": True,
            "mongoserver": "mongodb://localhost:27017/",
            "cacheaes": False
        }
                
        self.api = False
        self.auth = False
        
        self.cache = {}
        
        self.session = requests.Session()
        self.enabledebug = False
        self.options = dict(self.defoptions)
        self.mongoclient = pymongo.MongoClient(self.options["mongoserver"])
        self.setOptions(opts)
        
        global instance
        instance = self
        
        
    def getApi(self, fresh = False):
        if self.api != False and not fresh:
            return self.api
        self.api = api.Api(self.options)
        return self.api
        
    def setOptions(self, opts = {}):                
        if "configfile" in opts and opts["configfile"] != self.options["configfile"]:
            self.auth = False
            config = file_get_contents(opts["configfile"], True)
            
            if config:
                self.auth = file_get_contents(config["account"], True)
                self.auth["privateKeyObject"] = keys.PrivateKey(HexBytes(self.auth["privateKey"]))
                
                
        self.options.update(opts)
        if self.auth != False:
            self.options["auth"] = self.auth
        self.options["session"] = self.session
        self.options["mongoclient"] = self.mongoclient
        self.options["wrappercache"] = self.cache
        return self
        
    def call(self, endpoint, data = {}, opts = False):
        if opts != False:
            self.setOptions(opts)
        api = self.getApi()        
        res = api.call(endpoint, data, self.options)
        if self.enabledebug and not res:
            for e in api.apilog:
                try:
                    print(json.dumps(e,indent=4))
                except:
                    print(repr(e))
                print("")
        return res
        
    @staticmethod
    def getInstance():
        global instance
        if instance != None:
            return instance
        ApiWrapper()
        return instance
        
    def debug(self, enable = True):
        self.enabledebug = enable
