import queue
import time, datetime, math
import threading
import copy

class SCThreading:
    def __init__(self, opts):
        self.options = {
            "threads": 8,   # Desired number of threads
            "worker": None, # Worker callback
            "tasks": [],    # Initial Tasks
            "context": {},  # Thread context
            "retry": 0,     # Max retries for failed tasks
            "bundling": 1,   # How many tasks could get bundled
            "type": "fifo",  # FIFO, LIFO,
            "multiprocessing": False,
            "mp_gdict": None,
            "mp_lock": None,
            "mp_activetasks": None,
            "mp_taskpool": None,
            "mp_taskqueue": None
        }
        
        self.options.update(opts)
        self.mp = False
        self.multiprocess = None
        self.timings = {}
        self.contexts = {}
        
        if self.options["multiprocessing"] != False:
            self.mp = True
            self.multiprocess = self.options["multiprocessing"]
            self.gdict = self.options["mp_gdict"]
            self.lock = self.options["mp_lock"]
            self.activetasks = self.options["mp_activetasks"]
            self.taskpool = self.options["mp_taskpool"]
            self.taskqueue = self.options["mp_taskqueue"]
        else:
            self.gdict = {}        
            self.activetasks = {}        
            self.resultqueue = queue.Queue()
            if self.options["type"].lower() == "fifo":
                self.taskqueue = queue.Queue()
            elif self.options["type"].lower() == "lifo":
                self.taskqueue = queue.LifoQueue()
            else:
                raise ValueError("Invalid Queue Type")
            
            self.lock = threading.Lock()
            self.taskpool = {}
            
        
            
        self.tries = self.options["retry"] + 1
        self.errors = []
        self.resultcount = 0
        self.threads = []
        self.bundling = self.options["bundling"]
        
        self.taskid = 0
        
        
        
    def start(self, tasks = None):
        self.starttime = time.time()
        taskids = []
        if type(tasks) == list:
            for t in tasks:
                taskids.append(self.queue(t))
        else:
            for t in self.options["tasks"]:
                taskids.append(self.queue(t))
        
        self.threads = []        
        for i in range(self.options["threads"]):
            context = {}
            context = copy.deepcopy(self.options["context"])
            context["threadid"] = i
            t = threading.Thread(target=self.work,args=(i, self.options["worker"], context))
            self.threads.append(t)
            t.start()
            
        return taskids
            
    """
    Waits for Threads to terminate. Returns True if the threads are still alive after the given Timeout
    """
    def wait(self, timeout=None):
        if timeout != None:
            stop = time.time() + timeout
            while self.taskqueue.unfinished_tasks and time.time() < stop:
                time.sleep(0.05)
            
            if self.taskqueue.unfinished_tasks:
                return True
        
        self.taskqueue.join()
        for t in self.threads:
            self.taskqueue.put(None)
        
        
        self.taskqueue.join()
        
        for t in self.threads:
            t.join()
        
        
        return False
            
    def getDict(self):
        return self.gdict
        
    def getRQueue(self):
        return self.resultqueue
        
    def printStatus(self, forceraw = False):
        running = time.time() - self.starttime
        taskspersecond = self.resultcount / running
    
        r = "Results: " + str(self.resultcount)
        q = "Taskqueue: " + str(self.taskqueue.qsize())
        t = "Tasks / s : " + str(round(taskspersecond, 2))
        rt = "Runtime: " + str(datetime.timedelta(seconds=running))
        r = r.ljust(20)
        t = t.ljust(25)
        q = q.ljust(20)
        rt = rt.ljust(20)
        print(r + q + t +rt, end="\r")
            
    def work(self, i, worker, context):
        cancel = False
        tid = context["threadid"]
        while not cancel:
            self.lock.acquire()
            tasks = self.getTasks()
            validtasks = []
            trynums = []
            taskids = []
            for t in tasks:            
                if t == None:               
                    self.taskqueue.task_done()
                    cancel = True
                    break                                
                
                validtasks.append(t["t"])  
                trynums.append(t["trynum"])
                taskids.append(t["id"])
                self.activetasks[t["id"]] = False
                
            self.lock.release() 
                
            if self.mp:
                env = self.multiprocess
            else:
                env = self
                
            if len(validtasks) > 0:     
                context["taskids"] = taskids
                context["trynums"] = trynums
                
                successes = worker(env, context, validtasks)
                
                for i,s in enumerate(successes):
                    if not s:
                        t = validtasks[i]
                        trynum = trynums[i] + 1
                        tid = taskids[i]
                        if trynum < self.tries:
                            self.queue(t, trynum, tid)
                        else:
                            print("ERROR: " + repr(t) + " failed after " + str(trynum) + " tries")
                            self.errors.append("Task " + repr(t) + " failed with " + str(trynum) + " tries")                
                    self.taskqueue.task_done()
                    
        self.lock.acquire()
        try:
            self.contexts[str(tid)] = context
        finally:
            self.lock.release()
            
    def getTasks(self):
        if self.mp:
            return self.multiprocess.getTasks()
    
        try:
            t = self.taskqueue.get(False)
        except queue.Empty as e:
            return []
        tasks = [t]
        if t == None:
            return tasks
            
        if self.bundling > 1:
            for _ in range(1, self.bundling):
                try:
                    t = self.taskqueue.get(False)                    
                    tasks.append(t)
                    if t == None:
                        return tasks
                except queue.Empty as e:
                    break
        
        return tasks
                        
    def getErrors(self):
        return self.errors
        
    def resultCount(self):
        return self.resultcount
                
    def queue(self, task, trynum = 0, id = None):        
        if self.mp:
            return self.multiprocess.queue(task, trynum, id)
    
        self.lock.acquire()
        try:
            if id == None:
                id = self.taskid
                self.taskid += 1
            
            if id in self.activetasks and self.activetasks[id] == True:
                return id
                        
            self.taskqueue.put({"t": task, "trynum": trynum, "id": id})
            self.registerTask(id, task, True)
            self.activetasks[id] = True
        finally:
            self.lock.release()
            
        return id
            
    def registerTask(self, taskid, task, locked = False):
        if self.mp:
            return self.multiprocess.registerTask(taskid, task, locked)
        
        if not locked:
            self.lock.acquire()
        try:
            self.taskpool[taskid] = task
        finally:
            if not locked:
                self.lock.release()
    
    def getTaskById(self, taskid):
        if self.mp:
            return self.multiprocess.getTaskById(taskid)
    
        self.lock.acquire()        
        t = None
        try:
            if taskid in self.taskpool:
                t = self.taskpool[taskid]
        finally:
            self.lock.release()    
        return t
        
    def result(self, keyval, val = None, context = None, locked=False):
        if self.mp:
            return self.multiprocess.result(keyval, val)
        
        if not locked:
            self.lock.acquire()
        try:
            self.resultcount += 1
            if val == None:
                self.resultqueue.put(keyval)
            else:
                if keyval in self.gdict:
                    print("[WARN] Duplicate Result for key " + str(keyval))
                self.gdict[keyval] = val
        finally:
            if not locked:
                self.lock.release()
        
    def multiResult(self, valuedict, context = None):
        self.lock.acquire()
        try:
            for keyval, val in valuedict.items():
                self.result(keyval, val, context, True)
        finally:
            self.lock.release()
            
        
    def threadSafeDictWrite(self, key, value):
        self.lock.acquire()
        try:
            self.gdict[key] = value
        finally:
            self.lock.release()
            
    def threadSafeDictRead(self, key):
        self.lock.acquire()
        val = None
        try:
            val = self.gdict[key]
        finally:
            self.lock.release()
        return val
            
    def threadSafeDictMultiRead(self, keys):
        results = [None] * len(keys)
        self.lock.acquire()
        try:
            for i,key in enumerate(keys):
                if key in self.gdict:
                    results[i] = self.gdict[key]
        finally:
            self.lock.release()
        return results
        
    def threadSafeDictExists(self, key):
        self.lock.acquire()
        e = False
        try:
            e = key in self.gdict
        finally:
            self.lock.release()
        return e
        
    def timing(self, key, seconds):
        self.lock.acquire()        
        try:
            if key in self.timings:
                self.timings[key].append(seconds)
            else:
                self.timings[key] = [seconds]
        finally:
            self.lock.release()
        
    def getContexts(self):
        return self.contexts