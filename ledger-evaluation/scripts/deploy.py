import ujson
import sys, os, shutil
import time
import argparse
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from gclasses.procutils import shellexec
from gclasses.blockchain import Blockchain
from gclasses.timing import Timer
import pymongo

def file_get_contents(path, asJson):
    data = {}
    content = ""
    try:
        with open(path, 'r') as file:
            content = file.read()
    except Exception as e:
        return False

    if asJson:
        data = ujson.loads(content)
        return data
    return content

def file_put_contents(path, content, pretty=False):
    if not isinstance(content, str):
        if pretty:
            content = ujson.dumps(content, indent=4)
        else:
            content = ujson.dumps(content)

    try:
        with open(path, 'w') as file:
            file.write(content)
    except Exception as e:
        return False

    return True

def readinput(prompt):
    res = input(prompt + " ")
    return res

def clearFolder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def removeFile(path):
    try:
        os.unlink(path)
        return True
    except FileNotFoundError as e:
        return True
    except Exception as e:
        return False

def squote(s):
    return "'" + s.replace("'", "'\\''") + "'"

def apijson(url, data, attr=[]):
    res = os.popen('./dscc --url '+squote(url)+' --json '+squote(ujson.dumps(data))  + " " + (" ".join(attr))).read()
    try:
        json = ujson.loads(res)
        if json["code"] != 200:
            print("Error")
            print("API Code " + str(json["code"]))
            if "log" in json:
                for l in json["log"]:
                    print("  " + l)
        if "error" in json:
            print("Error: " + str(json["error"]))
        if "exception" in json:
            print("Exception: " + str(json["exception"]))
        return json
    except Exception as e:
        print("")
        print(repr(e))
        print(repr(res))
        return {
            "code": 500
        }

def printl(str):
    print(str.ljust(50), sep=' ', end='', flush=True)

def main():
    print("## Digital Supply Chain Deployment Tool")

    parser = argparse.ArgumentParser(description="Digital Supply Chain Deployment Tool")

    parser.add_argument("--authoritycount", "--authc", action="store", type=int, default=5, help="The number of ABE authorities to create")
    parser.add_argument("--attributecount", "--attrc", action="store", type=int, default=5, help="The number of Attributes per Authority to create")
    parser.add_argument("--reset", "-r", action="store_true", help="Reset existing database")
    parser.add_argument("--clearconfig", "-cc", action="store_true", help="Clear existing configuration")

    parser.add_argument("--quorumdir", "--qdir", action="store", default=None, help="Where is the Quorum Root directory? Quroum Setup skipped if not provided")
    parser.add_argument("--quorumnodes", "--q", action="store", default=2, type=int, help="How many Quroum Nodes to Deploy")
    parser.add_argument("--ether", action="store", default=20, type=int, help="How many Ether should each account get?")
    parser.add_argument("--smartcontract", "--sc", action="store", default=None, help="Truffle root directory")
    parser.add_argument("--timings", action="store", default="timings.json", help="Timing Output File")
    parser.add_argument("--baseurl", action="store", default="http://sensing.comsys.rwth-aachen.de/", help="The base URL to use")
    parser.add_argument("--deploycontractonly", action="store_true", help="Only re-deploy the ScData Contract on the Quorum Cluster")

    args = parser.parse_args()

    bu = args.baseurl

    if args.deploycontractonly:
        admin = file_get_contents("client/config/admin.json", True)
        api = file_get_contents("client/config/api.json", True)
        user = file_get_contents("client/config/user1.json", True)

        bc = Blockchain(admin, "client/config/ScData.json")
        print("  - Admin Ether Balance:    " + str(bc.getBalance(True)))
        print("  - Contract Address:       " + bc.getContractAddress())

        print("Setting API at contract...")
        thash1 = bc.transact("setApi", [api["address"]], {})
        print("  - Transaction Hash API:   " + str(thash1))

        print("Registering Client at contract...")
        thash2 = bc.transact("registerClient", [user["address"]], {})
        print("  - Transaction Hash Client:" + str(thash2))
        return

    t = Timer()


    interactive = False
    a = []


    doreset = args.reset
    clearconfig = args.clearconfig
    authcount = args.authoritycount
    attrcount = args.attributecount

    quorum = args.quorumdir != None

    #
    # RESET
    #
    t.start("reset")
    if doreset:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        printl("Resetting... ")
        client.drop_database("dsc")
        client.drop_database("dscclient")
        print("Ok")
    t.stop("reset")


    #
    # DELETE OLD CONFIG FILES
    #
    t.start("clearconfig")
    if clearconfig:
        clearFolder("client/config")
    t.stop("clearconfig")


    #
    # ENABLE AUTH OVERRIDE
    #
    print("")
    print("## Enabling Permission Override on the API")
    conf = file_get_contents("storage/config/main.conf", True)
    conf["permission-override"] = True
    file_put_contents("storage/config/main.conf", conf)

    #
    # CREATE CLIENT FILES
    #
    t.start("genaccount")
    print("")
    print("## Creating Admin Account")
    os.system("python3.7 ethereum/keygen/main.py Admin > client/config/admin.json")
    print("## Creating API Account")
    os.system("python3.7 ethereum/keygen/main.py API > client/config/api.json")
    print("## Creating User Account")
    os.system("python3.7 ethereum/keygen/main.py User > client/config/user1.json")
    configfile = {
        "account": "client/config/admin.json",
        "baseurl": bu
    }
    configfile2 = {
        "account": "client/config/api.json",
        "baseurl": bu
    }
    configfile3 = {
        "account": "client/config/user1.json",
        "baseurl": bu
    }
    file_put_contents("client/config/config.json", configfile)
    file_put_contents("client/config/config_api.json", configfile2)
    file_put_contents("client/config/config_user.json", configfile3)

    admin = file_get_contents("client/config/admin.json", True)
    api = file_get_contents("client/config/api.json", True)
    user = file_get_contents("client/config/user1.json", True)

    file_put_contents("storage/config/api_account.json", api)

    print("Admin: " + admin["address"])
    print("API:   " + api["address"])
    print("User:  " + user["address"])

    adminfile = file_get_contents("storage/config/authadmin.conf", True)
    if not adminfile:
        adminfile = {
            "name": "Authentication Admin",
            "permissions": ["auth/*", "auth/*/*", "reset"],
            "attributes": [],
            "active": True
        }
    adminfile["address"] = admin["address"]
    adminfile["pubkey"] = admin["publicKey"]

    t.stop("genaccount")

    #
    # INIT API
    #
    t.start("adminregister")
    print("## Registering Adminaccount to API")
    adminjson = {
        "pubkey": admin["publicKey"],
        "address": admin["address"],
        "name": "Adminaccount"
    }
    permissiondata = {
        "address": admin["address"],
        "permissions": ["*", "*/*", "*/*/*"]
    }
    printl("Registering... ")
    adminregister = apijson("auth/register", adminjson)
    if adminregister["code"] == 200:
        print("Ok")
    else:
        print("Error")
        return
    printl("Setting permissions... ")
    adminpermission = apijson("auth/permissions/add", permissiondata)
    if adminpermission["code"] == 200:
        print("Ok")
    else:
        print("Error")
        return

    print("## Disabling Permission Override")
    conf["permission-override"] = False
    file_put_contents("storage/config/main.conf", conf)

    t.stop("adminregister")

    #
    # REGISTER USER ACCOUNT
    #
    print("## Registering User Account to API")
    printl("Registering... ")
    userjson = {
        "pubkey": user["publicKey"],
        "address": user["address"],
        "name": "Default User Account"
    }
    userregister = apijson("auth/register", userjson)
    if userregister["code"] == 200:
        print("Ok")
    else:
        print("Error")
        return

    print("")
    print("")
    print("## Quroum Integration")
    if quorum:
        qdir = args.quorumdir
        qnum = args.quorumnodes
        ether = args.ether
        wei = str(ether) + "000000000000000000"
        sc = args.smartcontract
        print("Killing Geth...")
        print(shellexec("killall -HUP geth"))

        print("Resetting Quroum Cluster...")
        shellexec("rm -r " + qdir + "/node*/")

        print("Modifying genesis.json")
        genesis = file_get_contents(qdir + "/genesis.json", True)
        genesis["alloc"] = {
            user["address"]: {
                "balance": wei
            },
            api["address"]: {
                "balance": wei
            },
            admin["address"]: {
                "balance": wei
            }
        }
        file_put_contents(qdir + "/genesis.json", genesis, True)

        print("Creating Nodes")
        shellexec("mkdir -p " + qdir + "/keys")
        enodes = []
        staticnodes = []
        startscripts = []
        nodes = {}
        for n in range(qnum):
            port = str(21000 + n)
            raftport = str(50000 + n)
            rpcport = str(22000 + n)

            nodeid = n + 1
            nodename = "node" + str(nodeid).rjust(2, "0")

            print(" Creating " + nodename)

            keyfile = nodename + "key"
            shellexec("mkdir -p " + qdir + "/" + nodename)
            shellexec("cd " + qdir + " && bootnode --genkey=keys/" + keyfile + " && cp keys/" + keyfile + " " + nodename + "/nodekey")
            shellexec("cd " + qdir + " && bootnode --nodekey=" + nodename + "/nodekey --writeaddress > " + nodename + "/enode")
            enode = file_get_contents(qdir + "/" + nodename + "/enode", False).strip()
            enodes.append(enode)
            staticnodes.append("enode://" + enode + "@127.0.0.1:"+port+"?discport=0&raftport="+raftport)


            shellexec("cd " + qdir + " && geth --datadir=" + nodename + " init genesis.json")

            nodes[nodename] = {
                "port": port,
                "raftport": raftport,
                "rpcport": rpcport,
                "nodeid": nodeid,
                "nodeindex": n,
                "name": nodename,
                "enode": enode,
                "startscript": qdir + "/start_" + nodename + ".sh"
            }

            script1 = "PRIVATE_CONFIG=ignore nohup geth --datadir "+nodename+" --nodiscover --verbosity 5 --networkid 31337 --raft --raftport "+raftport+" --rpc --rpcaddr 0.0.0.0 --rpcport "+rpcport+" --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --emitcheckpoints --port "+port+" >> "+nodename+".log 2>&1 &"
            script2 = "PRIVATE_CONFIG=ignore geth --datadir "+nodename+" --nodiscover --verbosity 5 --networkid 31337 --raft --raftport "+raftport+" --rpc --rpcaddr 0.0.0.0 --rpcport "+rpcport+" --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --emitcheckpoints --port "+port
            prefix = '#!/bin/bash\ncd "${0%/*}"\n'
            script1 = prefix + script1
            script2 = prefix + script2
            file_put_contents(qdir + "/start_" + nodename +".sh", script1)
            file_put_contents(qdir + "/start_" + nodename +"_foreground.sh", script2)
            shellexec("chmod +x " + qdir + "/start_" + nodename +".sh")
            shellexec("chmod +x " + qdir + "/start_" + nodename +"_foreground.sh")

        print(" Nodes Created")
        print(" Starting Nodes")
        file_put_contents(qdir + "/static-nodes.json", staticnodes, True)
        for nodename in nodes:
            shellexec("cp " + qdir + "/static-nodes.json " + qdir + "/" + nodename + "/")
            shellexec(qdir + "/start_"+nodename+".sh", True)
        print(" Start Scripts executed")

        print("Truffle Integration")
        if sc != None:
            #print("  Clearing Truffle Build Artifacts")
            #shellexec("rm -r " + sc + "/build/")
            print("  Modifying truffle Configuration")
            tconf = file_get_contents(sc + "/truffle-config-template.js", False)
            tconf = tconf.replace("%ADMINPRIVKEY%", format(int(admin["privateKey"], 0), 'x'))
            file_put_contents(sc + "/truffle-config.js", tconf)
            print("  Running Truffle Migration with Admin Account...")
            t.start("trufflemigrate")
            migrate = shellexec("cd " + sc + " && truffle migrate --network quorum")
            t.stop("trufflemigrate")
            print("  Saving Migration Log to " + sc + "/migration.log")
            file_put_contents(sc + "/migration.log", migrate)
            print("  Copying ABI...")
            if os.path.isfile(sc + "/build/contracts/ScData.json"):
                shellexec("rm client/config/ScData.json")
                shellexec("rm storage/config/ScData.json")
                shellexec("cp " + sc + "/build/contracts/ScData.json client/config/")
                shellexec("cp " + sc + "/build/contracts/ScData.json storage/config/")
                print("Setting up BC connection")
                bc = Blockchain(admin, "client/config/ScData.json")
                print("  - Admin Ether Balance:    " + str(bc.getBalance(True)))
                print("  - Contract Address:       " + bc.getContractAddress())

                print("Setting API at contract...")
                t.start("setApi")
                thash1 = bc.transact("setApi", [api["address"]], {})
                print("  - Transaction Hash API:   " + str(thash1))
                t.stop("setApi")

                print("Registering Client at contract...")
                t.start("setClient")
                thash2 = bc.transact("registerClient", [user["address"]], {})
                t.stop("setClient")
                print("  - Transaction Hash Client:" + str(thash2))
            else:
                print("Compilation error")
        else:
            print("  Skipped")

    else:
        print("  Skipped")

    print("")
    print("## Deployment complete!")
    printl("Gathering results... ")
    accounts = apijson("auth/list", {})
    authorities = apijson("abe/authorities/list", {})

    if accounts["code"] == 200 and authorities["code"] == 200:
        print("Ok")
    else:
        print("Could not gather information")
        return

    print("# Accounts registered at storage:")
    print("("+str(len(accounts["auths"]))+" in total)")
    print("")
    for acc in accounts["auths"]:
        print("  " + acc["address"] + "  -  " + acc["name"])
    print("")
    print("")
    print("# Authorities registered at storage:")
    print(str(len(authorities["authorities"]))+" in total")
    print("")
    t.saveToFile(args.timings)
    print("# Timings saved at " + args.timings)

if __name__ == "__main__":
    main()
