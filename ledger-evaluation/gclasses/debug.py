DEBUG_MODE = True

def output(type, msg):
    if DEBUG_MODE:
        print("[" + type + "]   " + str(msg))

def error(msg):
    output("ERR", msg)
    
def info(msg):
    output("INF", msg)

def verbose(msg):
    output("VBS", msg)

def warning(msg):
    output("WRN", msg)
