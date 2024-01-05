import ujson
import sys, os

def file_get_contents(path, asJson = False):
    data = {}
    content = ""
    try:
        with open(path, 'r') as file:
            content = file.read()
    except Exception as e:
        return False
        
    if asJson:
        data = ujson.loads(content)
        return data
    return content

def file_put_contents(path, content):
    if not isinstance(content, str):
        content = ujson.dumps(content)
        
    try:
        with open(path, 'w') as file:
            file.write(content)
    except Exception as e:
        return False
    
    return True
    
def clearFolder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)
            
def removeFile(path):
    try:
        os.unlink(path)
        return True
    except FileNotFoundError as e: 
        return True
    except Exception as e:
        return False