def getDictValue(key, dict):
    if isinstance(key, str):
        key = key.split(".")
    
    if len(key) == 0 or key[0] == "":
        return dict
        
    if key[0] in dict:
        if len(key) == 1:
            return dict[key[0]]
        else:
            return getDictValue(key[1:], dict[key[0]])
        
    return None
            
def setDictValue(key, val, dict):
    if isinstance(key, str):
        key = key.split(".")
    
    if len(key) == 0 or key[0] == "":
        return False
        
    if len(key) == 1:
        dict[key[0]] = val
        return True
    if not key[0] in dict:
        dict[key[0]] = {}
    
    return setDictValue(key[1:], val, dict[key[0]])
            
def popDictKey(key, dict):
    if isinstance(key, str):
        key = key.split(".")
    
    if len(key) == 0 or key[0] == "":
        return False
        
    if key[0] in dict:
        if len(key) == 1:
            del dict[key[0]]
            return True
        else:
            return popDictKey(key[1:], dict[key[0]])
        
    return False