import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
sys.path.insert(0,currentdir + "/api")

from api import Api
from classes.argparser import ArgParser
import gclasses.debug as debug
import gclasses.fileutils as fileutils
from gclasses.blockchain import Blockchain
import gclasses.fingerprint as fingerprint
import ujson
import sys
import time

def main():
    startTime = time.time()
    argparser = ArgParser()
    args = argparser.getParser().parse_args()
    
    configfile = args.configfile
    config = {}
    try:
        with open(configfile, 'r') as file:
            config = ujson.loads(file.read())
    except Exception as e:
        debug.error("Invalid Configfile - " + repr(e) + " " + configfile)
    
    opts = config
    
    if "account" in config:
        acctfile = config["account"]
        del opts["account"]
        try:
            with open(acctfile, "r") as file:
                opts["auth"] = ujson.loads(file.read())
        except Exception as e:
            debug.error("Invalid Accountfile " + acctfile + " - " + repr(e))
        
    api = Api(opts)
    
    endpoint = args.endpoint
    if endpoint == None:
        debug.info("No endpoint given - exiting")
        sys.exit()
    
    data = args.data
    if isinstance(data, str):
        data = ujson.loads(data)
    
    stdindata = {}
    if args.readstdin:
        stdindata = ujson.load(sys.stdin)
        
    data = {**data, **stdindata}
    params = args.param
    for paramstr in params:
        param = paramstr.split(":", 1)
        if len(param) == 2:
            data[param[0]] = param[1]
            
    opts = {
        "type": args.type,
        "policy": args.policy,
        "encrypt": args.encrypt,
        "encryptprefix": args.encryptprefix,
        "decrypt": args.decrypt,
        "configfile": args.configfile,
        "addscsig": not args.disablescsignature,
        "addfingerprint": not args.disablefingerprinting,
        "rpcprovider": args.rpcprovider,
        "requestbc": not args.disableblockchain
    }
        
    response = api.call(endpoint, data, opts)
    endTime = time.time()
    try:
        if not isinstance(response, dict):
            rjson = {"api": "No Response", "code": -1}
        else:
            rjson = response
        rjson["client-runtime"] = (endTime - startTime)
        #rjson["client-log"] = api.apilog
        print(ujson.dumps(rjson, indent=4))
    except Exception as e:
        print(repr(response))
        print(repr(e))  
    
if __name__ == "__main__":
    main()
