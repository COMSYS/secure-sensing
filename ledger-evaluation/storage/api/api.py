import os,sys
import re
from result import ApiResult
from urllib.parse import parse_qs
import ujson
import hexbytes
from eth_account import Account
from eth_account.messages import encode_defunct
import time
from auth import Auth
import traceback
import config
sys.path.insert(0, config.parentdir)
from gclasses import fingerprint
from gclasses.blockchain import Blockchain
from db.Mongo import Mongo as Mongo
from ethereum.sign import validateSignatureStr

class Api:
    def handle(self, args):
        self.res = ApiResult()
        environ = args["env"]
        args["api"] = self
        self.args = args

        self.config = None

        startTime = time.time()

        # Load Config
        try:
            with open("../config/main.conf", "r") as f:
                self.config = ujson.loads(f.read())
        except Exception as e:
            self.res.log("Config could not be loaded")
            return res.send(500)

        # REQUEST BODY PARSING
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0

        request_body = environ['wsgi.input'].read(request_body_size)

        try:
            args["userargs"] = ujson.loads(request_body)
            args["payload"] = args["userargs"]["data"]["payload"]
            args["data"] = args["userargs"]["data"]
        except Exception as e:
            self.res.log(repr(e) + " (Body Parsing)")
            args["userargs"] = {}
            args["payload"] = {}
            args["data"] = {}

        # GET VALUE PARSING
        d = parse_qs(environ["QUERY_STRING"])
        for key, val in d.items():
            if len(val) == 1:
                args["getargs"][key] = val[0]
            elif len(val) > 1:
                args["getargs"][key] = val

        validSig = False
        address = False

        if "signature" in args["userargs"]:
            # Validate Signature
            if not self.validateSignature(args["userargs"]):
                self.res.code(401)
                return self.res.send()
            validSig = True
            address = args["userargs"]["data"]["signature_address"]
        else:
            self.res.log("No signature given")

        self.auth = Auth(address, validSig, self.config)
        if self.auth.isValid():
            self.res.log("Authenticated as " + self.auth.getAccountName())
        else:
            self.res.log("Authentication failed")

        self.res.set("request_args", args["userargs"])
        self.args = args
        #self.res.set("callnum", args["callnum"])

        try:
            if not self.validate(args):
                imp = "fcts.error.invalidpath"
            else:
                imp = "fcts." + (".".join(args["path"]))

            try:
                module = self.importfct(imp)
            except ModuleNotFoundError as e:
                module = self.importfct("fcts.error.notfound")
                self.res.log(repr(e))

            run = getattr(module, "run")

            ret = run(args)
        except Exception as inst:
            tb = traceback.format_exc()
            self.res.log(tb)
            module = self.importfct("fcts.error.internal")
            run = getattr(module, "run")
            args["exception"] = inst
            ret = run(args)

        endTime = time.time()
        self.res.set("api-runtime", endTime - startTime)

        return self.res.send()

    def importfct(self, name):
        m = __import__(name)
        for n in name.split(".")[1:]:
            m = getattr(m, n)
        return m

    """
    Checks whether the given path is a valid path, i.e. every part only consists of letters
    """
    def validate(self, args):
        if not "path" in args:
            return False

        p = re.compile('[a-z0-9]+')
        path = args["path"]
        for part in path:
            if p.fullmatch(part) == None:
                return False
        if not "endpoint" in args["data"]:
            return False

        return args["data"]["endpoint"] == "/".join(path)

    """
    Validates the signature of the API call.
    This covers authentication as well as integrity protection.
    Returns True iff the signature matches the public key and the 'data' part integrity has been verified.
    """
    def validateSignature(self, data):
        signature = data["signature"]
        json = ujson.dumps(data["data"])
        msghash = encode_defunct(text=json)

        vrs = (signature["v"], signature["r"], signature["s"])

        address = Account.recover_message(msghash, vrs=vrs)
        if (address == data["data"]["signature_address"]):
            timeout = self.config["signature-timeout"]
            # X seconds for time difference and high latency
            # Additional random NONCE prevents replay attacks

            # TODO: NONCE VALIDATION

            offset = abs(data["data"]["signature_time"] - time.time())

            if offset < timeout:
                self.res.log("Signature time offset in acceptable range: " + str(offset) + "s < " +str(timeout) + "s")
            else:
                self.res.log("Signature time offset violated: " + str(offset) + "s >= " +str(timeout) + "s")
                return False

            self.res.log("Signature verified")
            return True

        self.res.log("Signature invalid!")
        return False

    """
    Checks if the keys exists in the payload parameters for the specified arguments.
    If an argument is missing, the Result Code is set to 400 (Bad Request), a log entry is made and the function returns False.
    Otherwise the function returns True
    """
    def requireArgs(self, *args):
        payload = {}
        if "payload" in self.args:
            payload = self.args["payload"]

        ret = True

        for arg in args:
            if not arg in payload:
                self.res.log("Argument Missing: " + arg)
                self.res.code(400)
                ret = False

        return ret

    def hasArgs(self, *args):
        payload = {}
        if "payload" in self.args:
            payload = self.args["payload"]

        for arg in args:
            if not arg in payload:
                return False

        return True

    def getArgs(self):
        payload = {}
        if "payload" in self.args:
            payload = self.args["payload"]
        return payload

    def validateClientFingerprint(self, fp, sig):
        return validateSignatureStr(fp, sig, self.auth.address)


    def handleFingerprint(self, dataid, version):
        p = self.args["payload"]
        d = self.args["data"]
        dataid = str(dataid)
        if "__request_blockchain" in d and d["__request_blockchain"]:
            apidict = fingerprint.buildDictApi(self.args)
            fp = fingerprint.fp(apidict)
            if self.config["instant-blockchain"]:
                bc = Blockchain("../config/api_account.json", "../config/ScData.json")
                rtype = bc.rtypeToEnum(apidict["_type"])
                transactionhash = bc.transact("addFingerprintApi", [dataid, version, self.auth.address, rtype, fp])
                self.res.set("__bctx", True)
                self.res.set("__bcfp", fp)
                self.res.set("__bctxhash", transactionhash)
            else:
                bcdict = {
                    "fp": fp,
                    "rtype": apidict["_type"],
                    "version": version,
                    "address": self.auth.address,
                    "dataid": dataid,
                    "txhash": False,
                    "failed": False
                }
                mongo = Mongo("bcqueue")
                col = mongo.getCollection()
                col.insert_one(bcdict)
                self.res.set("__bctx", False)
                self.res.set("__bcfp", fp)
