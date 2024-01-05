def run(args):
    res = args["api"].res
    res.set("error", "You have specified an invalid path")
    res.set("path", "/".join(args["path"]))
    res.code(400)
    return True