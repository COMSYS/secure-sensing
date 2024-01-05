def run(args):
    res = args["api"].res
    if "exception" in args:
        ex = repr(args["exception"])
    else:
        ex = "Unknown"
    res.set("error", "An internal server error occured")
    res.set("exception", ex)
    res.set("path", "/".join(args["path"]))
    res.code(500)
    return True