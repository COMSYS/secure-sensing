import ujson
import config
import sys
sys.path.insert(0, config.parentdir)
import gclasses.gconfig as gconfig
import gclasses.dictutils as dictutils
import time

"""
Class for managing Versioning in data records
"""
class Versioning:
    """
    Creates a new version of the data record, applying all updates and returning a dict of $set instructions
    """
    def updateRecord(self, data, updates, actor, prefix = False, versionSig = None):
        if not prefix:
            prefix = []
        else:
            prefix = prefix.split(".")
    
        if not isinstance(updates, dict):
            raise ValueError("Invalid Updates Object")
            
        if not "__version" in data:
            data["__version"] = 1
        if not "__versioninfo" in data:
            data["__versioninfo"] = {
                "__v1": {
                    "timestamp": 0,
                    "actor": False
                }
            }
            
        version = data["__version"]
        versioninfo = data["__versioninfo"]
        
        nversion = version + 1
        nver = "__v" + str(nversion)
            
        record = data
        set = {}
        
        paths = []
        
        for k in updates:
            update = updates[k]
            if not isinstance(update, dict) or not "path" in update or not "value" in update or not isinstance(update["path"], str):
                raise ValueError("Invalid Update Object")
            p = update["path"].split(".")
            paths.append(update["path"])
            v = update["value"]
            fullpath = prefix + p
            curval = dictutils.getDictValue(fullpath, data)
            if curval == None:
                # This key has never existed
                curval = {
                    "__deleted": True
                }
            
            parval = dictutils.getDictValue(fullpath[:-1], data)
            if not isinstance(parval, dict):
                raise ValueError("Invalid path: " + ".".join(fullpath))
            
            
            if not isinstance(curval, dict) or not "__versioning" in curval:
                # Not versioned yet, wrap in versioning object
                versioning = {
                    "__versioning": {
                        "__v1": curval,
                        nver: v
                    }
                }
            else:
                # Versioning exists, add new version
                versioning = curval
                versioning["__versioning"][nver] = v
            
            set[".".join(fullpath)] = versioning
            dictutils.setDictValue(fullpath, versioning, data)
            
        versioninfo[nver] = {
            "timestamp": time.time(),
            "actor": actor,
            "__paths": sorted(paths)
        }
        
        if versionSig != None:
            versioninfo[nver].update(versionSig)
            
        set["__version"] = nversion
        data["__version"] = nversion
        set["__versioninfo"] = versioninfo
        data["__versioninfo"] = versioninfo
            
        return {
            "$set": set
        }
        
    
    """
    From a data record containing versioning information, this method reconstructs the specified version of the record.
    If no version is given, the most recent version is used.
    """
    def getRecord(self, data, version = False):
        if not isinstance(data, dict):
            raise ValueError("Invalid data - no dict")
        if not "__version" in data:
            raise ValueError("Invalid data - no version information")
        maxversion = data["__version"]
    
        if not version:
            version = maxversion
        else:
            version = int(version)
            if version > maxversion or version <= 0:
                raise ValueError("Invalid Version requested: " + str(version))        
        record = self.extractVersion(data, version)
        record["__version"] = version
        vstr = "__v" + str(version)
        if vstr in record["__versioninfo"]:
            record["__versioninfo"] = record["__versioninfo"][vstr]
        else:
            record["__versioninfo"] = False
        return record
            
    def extractVersion(self, data, version):
        if isinstance(data, dict):
            # Catch Versioning Objects
            if "__versioning" in data:
                versionval = self.findRecordValue(data, version)
                record = self.extractVersion(versionval, version)
                return record
            
            # No Versioning Object. Recursion
            record = {}            
            for k in data:
                val = data[k]                               
                recordval = self.extractVersion(val, version)                
                # Has the key been deleted?
                if not isinstance(recordval, dict) or not "__deleted" in recordval:
                    record[k] = recordval
                
            return record
            
        if isinstance(data, list):
            record = []
            for item in data:
                recordval = self.extractVersion(item, version)
                if not isinstance(recordval, dict) or not "__deleted" in recordval:
                    record.append(recordval)
            return record
        
        # Default: Strings and Numbers
        return data
        
        
    def findRecordValue(self, record, version):
        if not isinstance(record, dict) or not "__versioning" in record:
            raise ValueError("No Versioning Object Wrapper given to findRecordValue")
            
        if version < 1:
            raise ValueError("Invalid Version requested: " + str(version))
        
        versioning = record["__versioning"]
        if not isinstance(versioning, dict):
            raise ValueError("No Versioning Object given to findRecordValue")
        
        if not "__v1" in versioning:
            raise ValueError("Versioning Object has no version 1: " + repr(versioning))
            
        tryversion = version
        while tryversion > 0:
            vstr = "__v" + str(tryversion)
            if vstr in versioning:
                return versioning[vstr]
            tryversion -= 1
        
        raise Exception("Version could not be extracted")
        