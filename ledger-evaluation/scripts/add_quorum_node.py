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
from gclasses.fileutils import file_get_contents, file_put_contents
import pymongo

def main():
    print("## Quorum Node Deployment Tool")

    parser = argparse.ArgumentParser(description="Quorum Node Deployment Tool")

    parser.add_argument("--quorumdir", "--qdir", action="store", required=True, help="Where is the Quorum Root directory?")
    parser.add_argument("--nodeid", "-n", action="store", required=True, type=int, help="Which Node do you want to create?")
    parser.add_argument("--confirm",action="store_true", help="Required. You know what you are doing?")

    args = parser.parse_args()
    if not args.confirm:
        print("This will not deploy the Quorum cluster!")
        print(" For this purpose, you have to use the deploy.py script")
        print("This script adds a new node to an already existing cluster")
        print("-n has to be the next Node ID, i.e. if you already have 4 nodes running, n should be 5!")
        print("If you know what you are doing, add the --confirm parameter")
        return

    n = args.nodeid - 1
    qdir = args.quorumdir

    port = str(21000 + n)
    raftport = str(50000 + n)
    rpcport = str(22000 + n)

    staticnodes = file_get_contents(qdir + "/static-nodes.json", True)
    print("Existing Nodes ("+str(len(staticnodes))+"):")
    print('\n'.join(staticnodes))
    nodeid = n + 1
    nodename = "node" + str(nodeid).rjust(2, "0")

    print(" Creating " + nodename)

    restartscript = 'killall geth\nsleep 5\n'
    for i in range(n+1):
        enodename = "node" +str(i+1).rjust(2, "0")
        restartscript += './start_' + enodename + '.sh\n'
    print("# Saving Restart Script...")
    file_put_contents(qdir + "/restart_all.sh", restartscript)
    shellexec("chmox +x " + qdir + "/restart_all.sh")

    keyfile = nodename + "key"
    shellexec("mkdir -p " + qdir + "/" + nodename)
    shellexec("cd " + qdir + " && bootnode --genkey=keys/" + keyfile + " && cp keys/" + keyfile + " " + nodename + "/nodekey")
    shellexec("cd " + qdir + " && bootnode --nodekey=" + nodename + "/nodekey --writeaddress > " + nodename + "/enode")
    enode = file_get_contents(qdir + "/" + nodename + "/enode", False).strip()
    #enodes.append(enode)
    enodeid = "enode://" + enode + "@127.0.0.1:"+port+"?discport=0&raftport="+raftport
    staticnodes.append(enodeid)
    print("# Saving Static Nodes")
    file_put_contents(qdir + "/static-nodes.json", ujson.dumps(staticnodes, indent=5))

    shellexec("cd " + qdir + " && geth --datadir=" + nodename + " init genesis.json")

    print("Node created. Register it at follows:")
    print("Connect to geth interface of existing node")
    print("Execute:")
    print("")
    print("raft.addPeer('"+enodeid+"')")
    print("")
    print("And keep the return value")

    invalid = True
    while invalid:
        x = input("What was the return value of the raft.addPeer() call?")
        try:
            raftid = int(x)
            invalid = False
        except:
            print("Not a number")

    script1 = "PRIVATE_CONFIG=ignore nohup geth --datadir "+nodename+" --nodiscover --verbosity 5 --networkid 31337 --raft --raftblocktime 250 --raftjoinexisting "+str(raftid)+" --raftport "+raftport+" --rpc --rpcaddr 0.0.0.0 --rpcport "+rpcport+" --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --emitcheckpoints --port "+port+" >> "+nodename+".log 2>&1 &"
    script2 = "PRIVATE_CONFIG=ignore geth --datadir "+nodename+" --nodiscover --verbosity 5 --networkid 31337 --raft --raftblocktime 250 --raftjoinexisting "+str(raftid)+" --raftport "+raftport+" --rpc --rpcaddr 0.0.0.0 --rpcport "+rpcport+" --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --emitcheckpoints --port "+port
    prefix = '#!/bin/bash\ncd "${0%/*}"\n'
    script1 = prefix + script1
    script2 = prefix + script2
    file_put_contents(qdir + "/start_" + nodename +".sh", script1)
    file_put_contents(qdir + "/start_" + nodename +"_foreground.sh", script2)
    shellexec("chmod +x " + qdir + "/start_" + nodename +".sh")
    shellexec("chmod +x " + qdir + "/start_" + nodename +"_foreground.sh")

    print("Start Script created. You can start the new node now.")

if __name__ == "__main__":
    main()
