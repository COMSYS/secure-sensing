from gclasses import fileutils
from gclasses import gconfig

from copy import copy

from web3 import Web3, HTTPProvider

class Blockchain:
    def __init__(self, account, abifile=None, rpc="127.0.0.1:22000", nonce=None):
        if type(account) == dict:
            self.account = account
        elif type(account) == str:
            self.account = fileutils.file_get_contents(account, True)
        else:
            raise ValueError("Invalid Account")

        self.w3 = Web3(HTTPProvider("http://" + rpc))

        self.abifile = abifile
        if abifile == None:
            self.abifile = gconfig.rootdir + "/client/config/ScData.json"

        self.abi = None
        self.caddress = None
        self.contract = None
        self.init(nonce)

    def init(self, nonce):
        # ACCOUNT
        self.privateKey = self.account["privateKey"]
        self.address = self.account["address"]
        if nonce == None:
            self.nonce = self.w3.eth.getTransactionCount(self.address)
        else:
            self.nonce = nonce

        # ABI
        abi = fileutils.file_get_contents(self.abifile, True)
        if not abi:
            raise ValueError("Invalid Abifile: " + self.abifile)
        self.abi = abi["abi"]

        # CONTRACT
        nid = list(abi["networks"].keys())
        if len(nid) > 0:
            cinfo = abi["networks"][nid[0]]
            self.caddress = cinfo["address"]
            self.contract = self.w3.eth.contract(self.caddress, abi=self.abi)
        else:
            raise ValueError("No network to connect to")

        self.f = self.contract.functions

    """
    Returns the contract's function object.
    Use as bc.f.myMethod(...).transact() or bc.f.myMethod(...).call() or via this function:
    bc.fct().myMethod(...).transact() or bc.fct().myMethod(...).call()
    """
    def fct(self):
        return self.contract.functions

    """
    Returns the current balance of the active account either in Ether or in Wei
    """
    def getBalance(self, asEther = False):
        bal = self.w3.eth.getBalance(self.address)
        if asEther:
            return self.w3.fromWei(bal, "ether")
        else:
            return bal

    def getContractAddress(self):
        return self.caddress

    def getNonce(self):
        return self.nonce

    def useNonce(self):
        n = self.nonce
        self.nonce += 1
        return n

    def transact(self, fct, fctargs, transactionargs = {}):
        transactionargs["gasPrice"] = 0
        transactionargs["gas"] = 758096384
        transactionargs["from"] = self.address
        transactionargs["nonce"] = self.useNonce()

        m = getattr(self.f, fct)
        t = m(*fctargs).buildTransaction(transactionargs)

        signed = self.w3.eth.account.sign_transaction(t, self.privateKey)
        self.w3.eth.sendRawTransaction(signed.rawTransaction)
        return self.w3.toHex(signed.hash)

    def prepare_transaction(self, fct, fctargs, transactionargs = {}):
        transactionargs["gasPrice"] = 0
        transactionargs["gas"] = 758096384
        transactionargs["from"] = self.address
        transactionargs["nonce"] = self.useNonce()

        m = getattr(self.f, fct)
        t = m(*fctargs).buildTransaction(transactionargs)

        signed = self.w3.eth.account.sign_transaction(t, self.privateKey)
        return signed

    def send_transaction(self, signed):
        self.w3.eth.sendRawTransaction(signed.rawTransaction)
        return self.w3.toHex(signed.hash)

    def send_transaction_async(self, signed):
        self.w3.eth.sendRawTransactionAsync(signed.rawTransaction)
        return self.w3.toHex(signed.hash)


    def make_hash(self, o):
        """
        Makes a hash from a dictionary, list, tuple or set to any level, that contains
        only other hashable types (including any lists, tuples, sets, and
        dictionaries).
        """

        if isinstance(o, (set, tuple, list)):
            return tuple([self.make_hash(e) for e in o])
        elif not isinstance(o, dict):
            return hash(o)

        new_o = copy.deepcopy(o)
        for k, v in new_o.items():
            new_o[k] = self.make_hash(v)

        return hash(tuple(frozenset(sorted(new_o.items()))))

    def rtypeToEnum(self, rtype):
        switcher = {
            "produce": 0,
            "produceUpdate": 1,
            "trade": 2,
            "tracingAdd": 3,
            "tracingUpdate": 4,
            "trackingAdd": 5,
            "trackingUpdate": 6
        }
        return switcher.get(rtype, 7)

    def rtypeByApiCall(self, endpoint):
        switcher = {
            "sc/produce/create": 0,
            "sc/produce/update": 1,
            "sc/trade/create": 2,
            "sc/tracing/add": 3,
            "sc/tracing/update": 4,
            "sc/tracking/add": 5,
            "sc/tracking/update": 6
        }
        return switcher.get(endpoint, 7)
