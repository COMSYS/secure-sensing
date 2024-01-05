from db.Mongo import Mongo as Mongo
from auth import Auth
from versioning import Versioning
from bson.objectid import ObjectId
import helper


"""
Update Tracking Information of a specific Produce Entry
"""
def run(args):
    res = args["api"].res
    api = args["api"]
    data = args["payload"]

    api.requireArgs("updates", "__verify_fp", "__verify_sig", "__verify_ts")

    updates = data["updates"]

    clientfp = data["__verify_fp"]
    clientsig = data["__verify_sig"]
    clientts = data["__verify_ts"]

    if not api.validateClientFingerprint(clientfp, clientsig):
        res.code(400)
        res.log("Invalid Singature")
        return

    versionSig = {
        "__verify_type": "trackingUpdate",
        "__verify_fp": clientfp,
        "__verify_sig": clientsig,
        "__verify_ts": clientts
    }

    docinfo = helper.verifyRecordAccess(args)

    if not docinfo:
        return

    doc = docinfo["doc"]
    id = docinfo["id"]
    col = docinfo["col"]

    if not isinstance(updates, dict):
        res.code(400)
        res.log("Invalid Updates")
        return False

    if not "_type" in doc or not doc["_type"] in ["produce", "trade"]:
        res.code(400)
        res.log("Invalid Data Type")
        return

    v = Versioning()
    try:
        set = v.updateRecord(doc, updates, api.auth.address, "_tracking", versionSig)
    except Exception as e:
        res.log(repr(e))
        res.code(400)
        return

    result = col.update_one({"_id": id}, set)
    doc2 = col.find_one({"_id": id})
    if result.modified_count == 0:
        res.code(500)
        res.log("No records modified")
    else:
        res.code(200)
        rec = v.getRecord(doc2)
        api.handleFingerprint(id, rec["__version"])
        res.set("data", rec)
