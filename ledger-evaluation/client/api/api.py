import ujson
import requests
import uuid
import time
import sys
import copy
from ethereum.sign import sign, signStr
import gclasses.fileutils as fileutils
import gclasses.procutils as procutils
import gclasses.dictutils as dictutils
import gclasses.gconfig as gconfig
import gclasses.fingerprint as fingerprint
from gclasses.blockchain import Blockchain
import wrapper
import pymongo

class Api:
    def __init__(self, opts):
        self.globalopts = {
            "baseurl": gconfig.baseurl,
            "mongoclient": None
        }
        self.globalopts = {**self.globalopts, **opts}
        # Authentication
        self.calloptions = {}
        self.apilog = []
        self.log(self.globalopts)
        self.log(opts)
        self.abedecrypttime = 0
        self.decryptiterations = 0

    def log(self, msg):
        #print(msg)
        self.apilog.append(msg)

    def call(self, endpoint, data = {}, options = {}):
        # Make a call to the API, with authentication and signatures
        callstart = time.time()
        self.abedecrypttime = 0
        self.decryptiterations = 0
        defaults = {
            "type": "post",
            "verify": False,
            "addAuth": True,
            "encrypt": [],
            "encryptprefix": "payload",
            "decrypt": False,
            "keepencrypted": False,
            "policy": "",
            "addscsig": True,
            "addfingerprint": True,
            "rpcprovider": None,
            "requestbc": True,
            "mongoserver": "mongodb://localhost:27017/",
            "mongodb": "dscclient",
            "mongodbcol": "bcqueue",
            "mongoclient": None,
            "cacheaes": False
        }
        # SC Calls
        sccalls = [
            "sc/produce/create",
            "sc/produce/update",
            "sc/trade/create",
            "sc/tracking/add",
            "sc/tracking/update",
            "sc/tracing/add",
            "sc/tracing/update"
        ]

        # Get the current options. Defaults have smallest priority, passed options the highest
        opts = {**defaults, **self.calloptions, **options}
        self.opts = opts

        #self.log(opts)

        data = {"data": {"payload": data, "endpoint": str(endpoint)}}
        self.log(data)

        sigtime = 0
        gsigtime = 0
        fpruntime = 0

        # Encrypt?
        encrypttime = 0
        if len(opts["encrypt"]) > 0:
            encryptstart = time.time()
            prefixes = {}
            defprefix = opts["encryptprefix"]
            enc = opts["encrypt"]

            for e in opts["encrypt"]:
                split = e.split("..")
                if len(split) == 1:
                    pref = defprefix
                    path = split[0]
                else:
                    pref = split[0]
                    path = split[1]

                if not pref in prefixes:
                    prefixes[pref] = [path]
                else:
                    prefixes[pref].append(path)

            opts["encrypt"] = enc
            encrypttime = time.time() - encryptstart
            #data["data"]["__encryptinfo"] = einfo

        # Fingerprinting and Signature of SC Calls
        fp = ""
        if endpoint in sccalls:
            addr = self.globalopts["auth"]["address"]
            if opts["addfingerprint"]:
                fpstart = time.time()
                d = fingerprint.buildDict(endpoint, data["data"]["payload"], addr)
                fp = fingerprint.fp(d)
                fpruntime = time.time() - fpstart
                data["data"]["payload"]["__verify_ts"] = d["_timestamp"]
                data["data"]["payload"]["__verify_fp"] = fp
                if opts["addscsig"]:
                    sigstart = time.time()
                    scsig = signStr(self.globalopts["auth"], fp)
                    sigtime = time.time() - sigstart
                    data["data"]["payload"]["__verify_sig"] = scsig

        # Request Blockchain Proof
        if opts["requestbc"]:
            data["data"]["__request_blockchain"] = True

        # Add authentication
        if opts["addAuth"]:
            gsigstart = time.time()
            data = self.addAuth(data)
            gsigtime = time.time() - gsigstart

        if not opts["type"] in ["post", "get"]:
            self.log("Invalid Request Type " + opts["type"])
            return False

        if "session" in opts:
            session = opts["session"]
            method = getattr(session, opts["type"])
        else:
            method = getattr(requests, opts["type"])

        url = self.globalopts["baseurl"] + str(endpoint)

        self.log(data)
        resp = method(url, verify=opts["verify"], json=data)

        try:
            resp = ujson.loads(resp.text)
            decryptstart = time.time()
            if opts["decrypt"]:
                if opts["keepencrypted"]:
                    orig = copy.deepcopy(resp)
                    self.decryptData(resp, ["request_args"], False, opts)
                    resp["__original_response"] = orig
                else:
                    self.decryptData(resp, ["request_args"], False, opts)
            resp["encrypt-runtime"] = encrypttime
            resp["fp-runtime"] = fpruntime
            resp["gsig-runtime"] = gsigtime
            resp["sig-runtime"] = sigtime
            resp["decrypt-runtime"] = time.time() - decryptstart
            resp["client-runtime"] = time.time() - callstart
            resp["abedecrypt-runtime"] = self.abedecrypttime
            resp["decrypt-iterations"] = self.decryptiterations
        except Exception as e:
            print(repr(resp))
            print(repr(e))
            return resp

        # Fingerprint to Blockchain
        if endpoint in sccalls:
            acct = self.globalopts["auth"]
            if opts["addfingerprint"] and opts["requestbc"]:
                if not "data" in resp:
                    resp["__client_error"] = "Response has no Version!"
                else:
                    client = self.getMongoDb(opts)
                    col = client[opts["mongodb"]][opts["mongodbcol"]]
                    version = resp["data"]["__version"]
                    dataid = resp["data"]["_id"]
                    #rtype = bc.rtypeByApiCall(endpoint)
                    bcdict = {
                        "fp": fp,
                        "rtype": endpoint,
                        "version": version,
                        "address": acct["address"],
                        "dataid": dataid,
                        "txhash": False,
                        "failed": False
                    }
                    col.insert_one(bcdict)

        return resp

    def setOptions(self, options):
        self.calloptions = options

    def addAuth(self, data):
        if not "auth" in self.globalopts:
            return data
        data["account"] = self.globalopts["auth"]["address"]
        data = self.sign(data)
        return data

    def sign(self, data):
        nonce = uuid.uuid4().hex + uuid.uuid1().hex
        ts = time.time()
        data["data"]["signature_nonce"] = nonce
        data["data"]["signature_time"] = ts
        data["data"]["signature_address"] = self.globalopts["auth"]["address"]
        #data["nonce"] = nonce
        #data["timestamp"] = ts
        data = sign(self.globalopts["auth"], data)
        return data

    def expandAttributes(self, authoritycache, attributes, silent=True):
        knownattributes = []
        unambiguous = []
        ambiguous = []
        unambiguousmapping = {}
        ambiguousmapping = {}

        parsedattributes = []

        for auth in authoritycache:
            if not "attributes" in auth:
                self.log("No Attributes for authority")
                return False
            for attr in auth["attributes"]:
                knownattributes.append(attr)
                name = attr.split(gconfig.attribute_delimiter)
                if len(name) == 2:
                    prefix = name[0]
                    if prefix in unambiguous:
                        ambiguous.append(prefix)
                        ambiguousmapping[prefix].append(attr)
                        unambiguous.remove(prefix)
                    elif not prefix in ambiguous:
                        unambiguous.append(prefix)
                        unambiguousmapping[prefix] = attr
                        ambiguousmapping[prefix] = [attr]

        invalidname = False
        result = []
        for a in attributes:
            if a in knownattributes:
                result.append({"short": a, "full": a})
            elif a in unambiguous:
                result.append({"short": a, "full": unambiguousmapping[a]})
            elif a in ambiguous:
                if not silent:
                    self.log("Ambiguous Attribute: " + a)
                    self.log("Matches attributes " + (", ".join(ambiguousmapping[a])))
                return False
            else:
                if not silent:
                    self.log("Unknown Attribute: " + a)
                return False

        return result

    def refreshAuthorityCache(self, opts):
        w = wrapper.ApiWrapper().setOptions({"configfile": opts["configfile"]})

        client = self.getMongoDb(opts)
        col = client["dscclient"]["cache"]

        authorities = w.call("abe/authorities/list")


        if not authorities or (not "authorities" in authorities):
            return False
        authoritycache = {
            "authorities": authorities["authorities"],
            "type": "authoritycache"
        }
        # Save
        col.insert_one(authoritycache)

        if "wrappercache" in opts:
            c = opts["wrappercache"]
            c["authoritycache"] = authoritycache["authorities"]

        return authoritycache["authorities"]

    def parsePolicy(self, policy):
        attributes = []
        policy = policy.replace("and", "AND").replace("or", "OR")
        attributes = policy.replace(" AND ", ",").replace(" OR ", ",").replace("(", "").replace(")", "").split(",")
        attributes = list(map(lambda x: x.strip(), attributes))
        return attributes

    """
    Creates a full list of keys that have to be encrypted.
    Dots are used as delimiter.
    """
    def expandKeys(self, data, opts):
        keys = opts["encrypt"]
        self.log(keys)
        fullkeys = []
        for key in keys:
            exp = key.split(".")
            if len(exp) == 1 and exp[0] == "":
                continue
            if exp[-1] == "*" or exp[-1] == "**":
                # Expand
                if len(exp) > 1:
                    path = exp[:-1]
                    subdict = dictutils.getDictValue(exp[:-1], data)
                else:
                    subdict = data
                    path = []

                if subdict == None:
                    self.log("Key Error: " + ujson.dumps(exp))
                    return False

                encryptKey = False
                if exp[-1] == "**":
                    encryptKey = True

                for k in subdict:
                    fullkeys.append({
                        "path": path + [k],
                        "encryptKey": encryptKey
                    })
            else:
                if exp[0][-1] == "*":
                    path = [exp[0][:-1]]
                    encryptKey = True
                else:
                    encryptKey = False
                    path = exp

                fullkeys.append({
                    "path": path,
                    "encryptKey": encryptKey
                })

        return fullkeys

    def softRefreshAuthorityCache(self, opts):
        c = None
        if "wrappercache" in opts:
            c = opts["wrappercache"]
            if "authoritycache" in c:
                return c["authoritycache"], False

        updated = False
        client = self.getMongoDb(opts)
        col = client["dscclient"]["cache"]

        authoritycache = col.find_one({"type": "authoritycache"})
        if (not authoritycache) or (not "authorities" in authoritycache):
            authoritycache = self.refreshAuthorityCache(opts)
            if not authoritycache:
                self.log("Could not refresh Authority-Cache")
                return False, False
            updated = True

        if c != None:
            c["authoritycache"] = authoritycache

        return authoritycache, updated

    def advancedAttributeExpansion(self, authoritycache, updated, opts):
        policyattributes = opts["policy"]
        policyattributes = self.parsePolicy(policyattributes)

        attributes = self.expandAttributes(authoritycache, policyattributes, not updated)
        if not attributes:
            if updated:
                self.log("Attributes could not be matched")
                return False, authoritycache
            authoritycache = self.refreshAuthorityCache(opts)
            if not authoritycache:
                self.log("Could not refresh Authority-Cache")
                return False, authoritycache
            updated = True
            attributes = self.expandAttributes(authoritycache, policyattributes, False)

        if not attributes:
            self.log("Could not match attributes")
            return False, authoritycache
        if len(attributes) != len(policyattributes):
            self.log("This should not happen. Attribute Parsing Error")
            return False, authoritycache
        return attributes, authoritycache

    def rebuildPolicy(self, attributes, opts):
        policy = opts["policy"]
        for attr in attributes:
            if attr["short"] != attr["full"]:
                policy = policy.replace(attr["short"], attr["full"])
        return policy

    def expandPolicy(self, policy, configfile):
        opts = {
            "policy": policy,
            "configfile": configfile,
            "mongoserver": "mongodb://localhost:27017/"
        }
        authoritycache, updated = self.softRefreshAuthorityCache(opts)
        if not authoritycache:
            return False

        attributes, authoritycache = self.advancedAttributeExpansion(authoritycache, updated, opts)
        if not attributes:
            return False

        # Rebuild Policy
        policy = self.rebuildPolicy(attributes, opts)
        return policy

    def getMongoDb(self, opts):
        client = None
        if "mongoclient" in opts and opts["mongoclient"] != None:
            client = opts["mongoclient"]
        elif "wrappercache" in opts and "mongoclient" in opts["wrappercache"]:
            client = opts["wrappercache"]["mongoclient"]
        if client == None:
            client = pymongo.MongoClient(opts["mongoserver"])

        if "wrappercache" in opts:
            opts["wrappercache"]["mongoclient"] = client


        return client
