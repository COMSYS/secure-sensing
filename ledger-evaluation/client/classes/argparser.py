import argparse

class ArgParser(object):
    def __init__(self):
        self.progname = "SC Client"
        self.versionstr = "0.1"
        self.progversion = "{0} {1}".format(self.progname, self.versionstr)
        self.parser = argparse.ArgumentParser(description="Client for the Digital Supply Chain API. Reads JSON Data from stdin", prog=self.progname)
        
        self.url()
        self.baseurl()
        self.type()
        self.configfile()
        self.data()
        self.param()
        self.readstdin()
        self.encrypt()
        self.decrypt()
        
        self.blockchain()
        
    def getParser(self):
        return self.parser


    def url(self):
        p = self.parser
        p.add_argument("--endpoint", "--url", metavar="ENDPOINT", action="store", 
            help="The API Endpoint to call"
        )

    def baseurl(self):
        p = self.parser
        p.add_argument("--baseurl", metavar="BASEURL", action="store", 
            help="Optional: Replace the API base URL. If not given, the config file value will be used"
        )
        
    def type(self):
        p = self.parser
        p.add_argument("--type", metavar="REQTYPE", action="store", default="post",
            help="The HTTP Method to use",
            choices=["post", "get", "put", "delete"]
        )
        
    def configfile(self):
        p = self.parser
        p.add_argument("--configfile", "-c", metavar="CONFIGFILE", action="store", default="client/config/config.json",
            help="The path of the configfile (JSON) to use"
        )
        
    def data(self):
        p = self.parser
        p.add_argument("--data", "--json", metavar="DATA", action="store", default={},
            help="JSON Input to use as data to pass as parameter to the API"
        )
        
    def param(self):
        p = self.parser
        p.add_argument("--param", "--parameter", "-p", metavar="PARAMETER", action="append", default=[],
            help="Additional parameter in the form key:value to pass to the API. Will override existing values given by --data"
        )
        
    def encrypt(self):
        p = self.parser
        p.add_argument("--encrypt", "-e", metavar="ENCRYPTION", action="append", default=[],
            help="data-path to encrypt. * to encrypt the whole payload, use 'key' to only encrypt the data for the given key. Use dot-notation to address sub-keys, * as wildcard (e.g. key.*). Using a double dot allows for multiple prefix selection (e.g. prefix..key1.*, prefix..key2)"
        )
        p.add_argument("--policy", metavar="POLICY", action="store", default="",
            help="Encryption Policy. Unknown attributes will lead to a re-fetch of available attributes. Unambiguous Attribute prefix suffice and will be replaced to include  the authority postfix"
        )
        p.add_argument("--encryptprefix", "-ep", metavar="ENCRYPTIONPREFIX", action="store", default="",
            help="Encryption Prefix. The base level where encryption should be applied for keys not containing a double dot (..)."
        )
        
    def decrypt(self):
        p = self.parser
        p.add_argument("--decrypt", "-d", action="store_true", default=False,
            help="Tries to decrypt the received payload if a format suitable for decryption is detected"
        )
        
    def readstdin(self):
        p = self.parser
        p.add_argument("--readstdin", "-r", 
                action="store_true",
                help="Set if you want to read JSON from StdIn")
                
    def blockchain(self):
        self.parser.add_argument("--rpcprovider", "--rpc", action="store", default="127.0.0.1:22000", help="IP and Port of the HTTP RPC Provider")
        self.parser.add_argument("--disablefingerprinting", "--nofp", "-nf", action="store_true", help="Disable Fingerprinting Mechanisms for SC calls")
        self.parser.add_argument("--disablescsignature", "--noscsig", action="store_true", help="Disable additional signature on Fingerprinting sets")
        self.parser.add_argument("--disableblockchain", "--nobc", action="store_true", help="Disable Blockchain proof of SC Requests")
        