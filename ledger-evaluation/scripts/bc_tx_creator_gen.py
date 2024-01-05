import json
import sys, os, inspect, copy, math


# Set path in order for imports to work
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import gclasses.fileutils as fileutils
import gclasses.fingerprint as fingerprint
from gclasses.blockchain import Blockchain
from gclasses.timing import Timer
from gclasses.procthreads import SCMultiprocessing

import argparse

from web3.auto.gethdev import w3

from web3.datastructures import MutableAttributeDict


def worker(threading, context, tasks):
    
    # Performance Evaluation
    if context["mp"]:
        if "timing" in context:
            # Use existing timer
            eval_timer_thread = context["timing"]
        else:
            # Create a new one
            eval_timer_thread = Timer(False)
            context["timing"] = eval_timer_thread

    # Check if blockchain exists and use it from context
    if "bc" in context:
        bc = context["bc"]
    else:
        # Otherwise create a new instance
        port = 22000 + (context["processid"] % context["nodecount"])
        # print("Node Port: " + str(port))
        
        bc = Blockchain(context["account"], None, "127.0.0.1:"+str(port), 0)

        # Assign blockchain obj for later usage
        context["bc"] = bc

    successes = []

    # Start measurement for thread
    # t.start("thread")

    for i,ptx in enumerate(tasks):
        
        # Measure time for transaction itself
        eval_timer_thread.start("transact")
        txhash = bc.send_transaction(ptx)
        eval_timer_thread.stop("transact")

        successes.append(True)
        
        # Print transaction hash as result
        # print(txhash)
            
        # Add timer result
        threading.result(txhash, True)
        threading.result("time", eval_timer_thread)


    # Stop measurement
    # t.stop("thread")

    return successes

def start_workers(args,transactions,bid,account,timing):
    # Configure worker and parameters for calling it
    opts = {
        "processes": args.processes,
        "threads": None,
        "worker": worker,
        "tasks": transactions,
        "context": {
            "args": copy.deepcopy(args),
            "mp": True,
            "account": account,
            "nodecount": args.nodecount
        },
        "retry": 5,
        "bundling": math.floor(len(transactions)/args.processes),
        "timingfile": args.timing.replace(":bid", str(bid)),
        "usemongo": False
    }

    
    threading = SCMultiprocessing(opts)

    threading.start()

    # Time measurement for parallel computation
    # timing.start("threading")
    threading.wait()
    # timing.stop("threading")

    threading.printStatus(True)

    # Append to existing timer object
    timing.combine(threading.getDict()["time"])

    errors = threading.getErrors()
    if len(errors) > 0:
        for e in errors:
            print(e)
    return threading.getDict()

# Main entry point for transaction creation
def main():

    # Default configuration file for api access
    # This is the `Quorum` account
    configfile = "storage/config/api_account.json"


    parser = argparse.ArgumentParser(description="Data Record Reception")

    parser.add_argument("--account", action="store", default=configfile, help="The Account File of the User to use for Transactions")
    parser.add_argument("--mode", action="store", default="api", choices=["api", "client"], help="In which mode to operate")
    parser.add_argument("--tries", action="store", default=1, type=int, help="How often should we try to perform the transaction before giving up?")
    parser.add_argument("--processes", action="store", default=1, type=int, help="How many processes to use for transaction provision")
    parser.add_argument("--prepare", action="store", type=int, default=1, help="How many fingerprints should be prepared before issuing them")
    parser.add_argument("--txbundle", action="store", type=int, default=1, help="How many fingerprints per transaction?")
    parser.add_argument("--maxtx", action="store", type=int, default=0, help="Stop after this amount of transactions. 0 = No limit")
    parser.add_argument("--preponly", action="store_true", help="Set to only prepare transactions but not deleting them from the database and not sending them")
    parser.add_argument("--timing", action="store", default=None, help="File to save timing information to")
    parser.add_argument("--record", action="store", default=None, help="Only search for transactions regarding a specific record")
    parser.add_argument("--nodecount", action="store", default=1, type=int, help="Number of nodes (i.e., Node Port 21000 + NodeID)")
    parser.add_argument("--txsize", action="store_true", help="Show the size of a transaction in Bytes")

    # Parse arguments for later usage
    args = parser.parse_args()

    # Sanity check for custom provided account
    acctfile = args.account
    account = fileutils.file_get_contents(acctfile, True)
    if not account:
        print("Invalid Account")
        return

    # Method is defined in solidity file and chosen
    # based on the mode in which a transaction is created
    method = ""    
    
    if args.mode == "api":
        # Select API specific function
        method = "addFingerprintApi"
        
        modestr = "API"
        filter = {}
    else:
        # Client specific function
        method = "addFingerprintClient"
        
        modestr = "Client"
        filter = {"address": account["address"]}

    if args.record != None:
        filter["dataid"] = args.record
    
    txcount = 0


    print("== Blockchain TX Creator ==")
    print(modestr + " Mode")
    
    # Create blockchain object with account as parameter 
    # Get binary interface automatically from `client/config/ScData.json`
    # which was compiled in `DEPLOY_ALL.sh`
    bc = Blockchain(account)
    
    # Start evaluation timer
    eval_timer = Timer(False)

    compute_transactions = True
    bid = 1

    while compute_transactions:
        pprepared = []
        
        
        # eval_timer.start("bundle")
        for i in range(args.prepare):
            
            # Generation: use fake data and create fingerprints
            # to mimic data base retrievals

            # Load json fakedata
            fakedata1k_file = json.load(open('./json_data/fakedata1k.json'))
            
            # Compute fingerprint of file
            fd_fp = fingerprint.fp(fakedata1k_file)

            # print(fakedata1k_file)
            # print(fd_fp)

            # Build data
            data = {
                "fp": fd_fp, # String of 28 Byte long integer
                "dataid": "123456788765432134567890", # String of 12 Byte hex for dataid 
                "version": 1, # uint version
                "address": "0x5cb738DAe833Ec21fe65ae1719fAd8ab8cE7f23D", # Client ID for user1 - a 20 byte long hex
                "rtype": "produce", # one of `PRODUCE,PRODUCEUPDATE,TRADE,TRACEADD,TRACEUPDATE,TRACKADD,TRACKUPDATE,INVALID`
            }

            # Decode fingerprint and dataid from strings to byte representations
            fp = bytes.fromhex(data["fp"])
            dataid = bytes.fromhex(data["dataid"])
                
            # Start timer for preparation
            eval_timer.start("prepare")

            # Assume API mode and compute preparation for ABI Call
            rtype = bc.rtypeToEnum(data["rtype"])
            
            # Returns a signed transaction with the instantiated bc's private key
            tx = bc.prepare_transaction(method, [dataid, data["version"], data["address"], rtype, fp])

            if args.txsize:
                print("RawTransaction: " + str(tx["rawTransaction"]))
                print("Size in Bytes: " + str(len(tx["rawTransaction"])))

            eval_timer.stop("prepare")
            
            txcount += 1

            # Break on maximum specified txs
            if args.maxtx > 0 and txcount >= args.maxtx:
                # print("Maximum TX reached")
                compute_transactions = False

            # Use a mutable dict to circumvent immutability error of
            # library, which fails otherwise.
            pprepared.append(MutableAttributeDict(tx))
            
            

        # eval_timer.stop("bundle")

        # print("Prepared " + str(txcount) + " Transactions - bundle completed")
        
        # Submit transaction after preparation if not specified otherwise
        if not args.preponly:
            # print("Submitting TX")
            # eval_timer.start("txbundle")
        
            # Start worker that processes the bundled transactions
            txhashes = start_workers(args, pprepared, bid, account,eval_timer)
            
            bid += 1
            # eval_timer.stop("txbundle")


    if args.timing != None:
        eval_timer.saveToFile(args.timing.replace(":pid", "main").replace(":bid", "main"))
        print("PREPARATION AVG:    " + str(eval_timer.getAvg("prepare")))
        print("TRANSACTIONS / SEC: " + str( 1 / eval_timer.getAvg("prepare")))

if __name__ == "__main__":
    main()
