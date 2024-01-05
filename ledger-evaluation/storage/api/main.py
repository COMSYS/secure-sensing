from api import Api
import sys
import ujson

def main():
    path = "--"
    uargs = {}
    if len(sys.argv) > 1:
        path = sys.argv[1]

    if len(sys.argv) > 2:
        print(sys.argv[2])
        try:
            uargs = ujson.loads(sys.argv[2])
        except ValueError as e:
            raise ValueError("JSON Parse: " + repr(e))

    args = {
        "path": path.split("/"),
        "userargs": uargs
    }
    api = Api()
    api.handle(args)

if __name__ == "__main__":
    main()
