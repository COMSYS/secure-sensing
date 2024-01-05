def run(args):
    res = args["api"].res
    res.set("error", "This function does not exists")
    res.set("path", "/".join(args["path"]))
    res.code(404)
    return True