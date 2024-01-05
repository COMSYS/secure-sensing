import sys,os
import ujson
from subprocess import Popen, PIPE, STDOUT, run
       
def squote(s):
    return "'" + s.replace("'", "'\\''") + "'"
    
def shellexec(cmd, detach=False, printErr = True):
    if detach:
        cmd = cmd.split(" ")
        res = Popen(cmd)
    else:
        res = run(cmd, capture_output=True, shell=True).stdout
    return res

def apijson(url, data={}, attr=[], silent=True):
    cmd = './dscc --url '+squote(url)+' -d --json '+squote(ujson.dumps(data))  + " " + (" ".join(attr))
    #res = os.popen(cmd).read()
        
    res = run(cmd, capture_output=True, shell=True).stdout
    silent = False
    
    try:
        json = ujson.loads(res)
        if json["code"] != 200:
            if not silent:
                print("Error")
                print("API Code " + str(json["code"]))
            if "log" in json and not silent:
                for l in json["log"]:
                    print("  " + l)
        if "error" in json and not silent:
            print("Error: " + str(json["error"]))
        if "exception" in json and not silent:
            print("Exception: " + str(json["exception"]))
        return json
    except Exception as e:
        if not silent:
            print("")
            print(repr(e))
            print(repr(res))
            print(cmd)
        return {
            "code": 500
        }
        
def jsonscript(file, params = [], quote = True):
    if quote:
        params = list(map(lambda x: squote(x), params))
    res = os.popen(file + " " + " ".join(params)).read()
    try:
        res = ujson.loads(res)
    except Exception as e:
        res = {
            "error": repr(e)
        }
    
    return res