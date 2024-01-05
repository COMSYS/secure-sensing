import time
import ujson
import hashlib
from ethereum.sign import validateSignatureStr
import gclasses.dictutils as dictutils

"""
Builds the Dictionary it. Information is extracted from the API Arguments Object
"""
def buildDictApi(args):
    endpoint = "/".join(args["path"])
    payload = args["payload"]
    clientAddress = args["api"].auth.address
    timestamp = payload["__verify_ts"]
    return buildDict(endpoint, payload, clientAddress, timestamp)

"""
Computes the Hash of a Dictionary
"""
def fp(d):
    s = ujson.dumps(d, sort_keys=True, ensure_ascii=True, double_precision=9, escape_forward_slashes=True, encode_html_chars=False)
    return hashlib.sha224(s.encode()).hexdigest()


"""
Builds a dictionary to fingerprint based on the API Call
"""
def buildDict(endpoint, payload, clientAddress, timestamp = None):
    if timestamp == None:
        timestamp = time.time()

    if endpoint == "sc/produce/create":
        return produceCreate(payload, clientAddress, timestamp)
    elif endpoint == "sc/produce/update":
        return produceUpdate(payload, clientAddress, timestamp)
    elif endpoint == "sc/trade/create":
        return tradeCreate(payload, clientAddress, timestamp)
    elif endpoint == "sc/tracking/add":
        return trackingAdd(payload, clientAddress, timestamp)
    elif endpoint == "sc/tracking/update":
        return trackingUpdate(payload, clientAddress, timestamp)
    elif endpoint == "sc/tracing/add":
        return tracingAdd(payload, clientAddress, timestamp)
    elif endpoint == "sc/tracing/update":
        return tracingUpdate(payload, clientAddress, timestamp)

    return None

def produceCreate(payload, clientAddress, timestamp):
    batch = valOrDef(payload, "_batch", {"size": 1})
    policy = valOrDef(payload, "_policy", None)
    tracking = valOrDef(payload, "_tracking", {})
    tracing = payload["_tracing"]
    produce = payload["_product"]

    d = {
        "_timestamp": timestamp,
        "_type": "produce",
        "_producer": clientAddress,
        "_batch": batch,
        "_policy": policy,
        "_tracing": tracing,
        "_tracking": tracking,
        "_product": produce
    }
    return d

def produceUpdate(payload, clientAddress, timestamp):
    u = payload["_updates"]
    l = sorted(u.items(), key=lambda t: t[1]["path"])
    id = payload["_id"]
    updates = []
    for p in l:
        updates.append(p[1])

    d = {
        "_updates": updates,
        "_type": "produceUpdate",
        "_timestamp": timestamp,
        "_id": id
    }
    return d

def tradeCreate(payload, clientAddress, timestamp):
    batch = valOrDef(payload, "_batch", {"size": 1})
    policy = valOrDef(payload, "_policy", None)
    tracking = valOrDef(payload, "_tracking", {})
    recipient = payload["_recipient"]
    reference = payload["_reference"]

    d = {
        "_sender": clientAddress,
        "_timestamp": timestamp,
        "_type": "trade",
        "_reference": reference,
        "_recipient": recipient,
        "_batch": batch,
        "_policy": policy,
        "_tracking": tracking
    }
    return d

def trackingAdd(payload, clientAddress, timestamp):
    d = tracingAdd(payload, clientAddress, timestamp)
    d["_type"] = "trackingAdd"
    return d

def trackingUpdate(payload, clientAddress, timestamp):
    d = tracingUpdate(payload, clientAddress, timestamp)
    d["_type"] = "trackingUpdate"
    return d

def tracingAdd(payload, clientAddress, timestamp):
    u = payload["updates"]
    l = sorted(u.items(), key=lambda t: t[0])
    id = payload["_id"]
    updates = []
    for p in l:
        s = {"value": p[1]["value"]}
        updates.append(s)

    d = {
        "_updates": updates,
        "_type": "tracingAdd",
        "_timestamp": timestamp,
        "_id": id
    }
    return d

def tracingUpdate(payload, clientAddress, timestamp):
    u = payload["updates"]
    l = sorted(u.items(), key=lambda t: t[1]["path"])
    id = payload["_id"]
    updates = []
    for p in l:
        updates.append(p[1])

    d = {
        "_updates": updates,
        "_type": "tracingUpdate",
        "_timestamp": timestamp,
        "_id": id
    }
    return d


def hasKeys(dict, *keys):
    for k in keys:
        if not k in dict:
            return False
    return True

def valOrDef(dict, key, default):
    if key in dict:
        return dict[key]
    return default

def dictDiff(dictA, dictB):
    return { k : dictB[k] for k in set(dictB) - set(dictA) }

def validateVersion(version, id):
    if not "__versioninfo" in version:
        raise ValueError("No version info")
    vinfo = version["__versioninfo"]
    v = version["__version"]
    d = None
    if hasKeys(vinfo, "__verify_ts", "__verify_fp", "__verify_sig", "__verify_type", "actor"):
        ts = vinfo["__verify_ts"]
        vfp = vinfo["__verify_fp"]
        sig = vinfo["__verify_sig"]
        rtype = vinfo["__verify_type"]
        clientAddress = vinfo["actor"]
    else:
        return False, "Invalid Version Info"

    if rtype in ["produce", "trade"]:
        if v != 1:
            return False, "Produce and Trade have to be Version 1"
        if rtype == "produce":
            d = produceCreate(version, clientAddress, ts)
        else:
            d = tradeCreate(version, clientAddress, ts)
    else:
        # Updates / Add
        if v <= 1:
            return False, "Version cannot be <= 1"

        test = {
            "_type": rtype,
            "_timestamp": ts,
            "_updates": None,
            "_id": id
        }

        if rtype == "produceUpdate":
            dnew = version["_product"]
        elif rtype in ["tracingUpdate", "tracingAdd"]:
            dnew = version["_tracing"]
        elif rtype in ["trackingUpdate", "trackingAdd"]:
            dnew = version["_tracking"]
        else:
            return False, "Invalid / Unsupported RequestType"

        updates = None

        paths = sorted(vinfo["__paths"])
        updates = []

        addMode = rtype in ["tracingAdd", "trackingAdd"]

        for p in paths:
            val = dictutils.getDictValue(p, dnew)
            if val == None:
                updates.append({"path": p, "value": {"__deleted": True}})
            else:
                if addMode:
                    updates.append({"value": val})
                else:
                    updates.append({"path": p, "value": val})


        test["_updates"] = updates
        d = test

    if d == None:
        return False, "No Dict could be created"

    myfp = fp(d)
    if myfp != vfp:
        return False, "Fingerprint Mismatch (" + str(myfp) + " vs " + vfp +")"

    if not validateSignatureStr(myfp, sig, clientAddress):
        return False, "Invalid Signature"

    return True, {"msg": "Fingerprint and Signature valid", "fp": myfp, "rtype": rtype}
