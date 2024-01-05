import queue
import math
import time, datetime
import multiprocessing
import curses
import copy
import pymongo
from gclasses.threads import SCThreading

def processworker(i, context, opts, q):
    o = {}
    o.update(opts)
    o["tasks"] = []
    threading = SCThreading(opts)
    threading.start()
    q.join()

class SCMultiprocessing:
    def __init__(self, opts):
        self.options = {
            "processes": 8,   # Desired number of Processes
            "worker": None, # Worker callback
            "tasks": [],    # Initial Tasks
            "context": {},  # Thread context
            "retry": 0,     # Max retries for failed tasks
            "bundling": 1,   # How many tasks could get bundled
            "type": "FIFO",
            "threads": None,
            "timingfile": False,
            "usemongo": False,
            "mongoserver": "mongodb://localhost:27017/",
            "mongodb": "procthreads",
            "mongodbcol": "procresults-" + str(time.time())
        }

        self.options.update(opts)
        self.stdscr = False
        #self.stdscr = curses.initscr()
        #curses.noecho()
        #curses.cbreak()

        self.mongo = None

        self.m = multiprocessing.Manager()
        self.timings = self.m.dict()
        self.timings["calls"] = []

        self.threads = self.options["threads"] != None
        self.threadcount = self.options["threads"]

        self.gdict = self.m.dict()
        self.activetasks = self.m.dict()

        self.contexts = self.m.dict()

        self.resultqueue = multiprocessing.JoinableQueue()
        if self.options["type"].lower() == "fifo":
            self.taskqueue = multiprocessing.JoinableQueue()
        else:
            raise ValueError("Invalid Queue Type")

        self.lock = multiprocessing.Lock()
        self.tries = self.options["retry"] + 1
        self.errors = self.m.list()
        self.resultcount = self.m.Value("resultcount", 0)
        self.resultcountodd = self.m.Value("resultcountodd", 0)
        self.resultcounteven = self.m.Value("resultcounteven", 0)
        self.activeresultcount = self.m.Value("activeresultcount", 0)
        self.processes = []
        self.bundling = self.options["bundling"]

        self.taskid = self.m.Value("taskid", 0)
        self.taskpool = self.m.dict()


    def start(self, tasks = None):
        self.starttime = time.time()
        taskids = []
        if type(tasks) == list:
            for t in tasks:
                taskids.append(self.queue(t))
        else:
            for t in self.options["tasks"]:
                taskids.append(self.queue(t))

        self.processes = []
        for i in range(self.options["processes"]):
            context = copy.copy(self.options["context"])
            context["threadid"] = i
            context["processid"] = i
            if self.threads:
                print("THREADS DETECTED!!!!!!!!!")
                o = {}
                o = copy.deepcopy(self.options)
                o["mp_gdict"] = self.gdict
                o["mp_lock"] = self.lock
                o["mp_activetasks"] = self.activetasks
                o["mp_taskpool"] = self.taskpool
                o["mp_taskqueue"] = self.taskqueue
                o["multiprocessing"] = self
                p = multiprocessing.Process(target=processworker,args=(i, context, o, self.taskqueue))
            else:
                p = multiprocessing.Process(target=self.work,args=(i, self.options["worker"], context))
            self.processes.append(p)
            p.start()

        return taskids

    def kill(self):
        if self.stdscr:
            curses.echo()
            curses.nocbreak()
            curses.endwin()

        for p in self.processes:
            p.terminate()

        for p in self.processes:
            p.join()

    """
    Waits for Processes to terminate. Returns True if the processes are still alive after the given Timeout
    """
    def wait(self, timeout=None):
        if timeout != None:
            stop = time.time() + timeout
            while not self.taskqueue._unfinished_tasks._semlock._is_zero() and time.time() < stop:
                time.sleep(0.05)

            if not self.taskqueue._unfinished_tasks._semlock._is_zero():
                return True

        #print("Waiting for Queue to be empty...")
        self.taskqueue.join()
        #print("Signaling Termination to Queue via 'None'...")
        for _ in self.processes:
            if self.threads:
                for _ in self.threadcount:
                    self.taskqueue.put(None)
            else:
                self.taskqueue.put(None)

        #print("Waiting for Queue to be empty (2)...")
        self.taskqueue.join()

        #print("Joining Processes...")
        for p in self.processes:
            p.join()

        if self.stdscr:
            curses.echo()
            curses.nocbreak()
            curses.endwin()

        #print("All processes terminated")
        return False


    def getDict(self):
        if self.options["usemongo"]:
            col = self.makeMongo()
            docs = col.find()
            res = {}
            for d in docs:
                if d["key"] in res:
                    print("Duplicate Key: " + str(d["key"]))
                res[d["key"]] = d["val"]
            col.drop()
            return res

        return self.gdict

    def getRQueue(self):
        return self.resultqueue

    def printStatus(self, forceRaw = False):
        running = time.time() - self.starttime
        taskspersecond = self.resultcount.value / running
        tm = math.floor(time.time())
        if tm % 2 == 0:
            taskslastsecond = self.resultcountodd.value
        else:
            taskslastsecond = self.resultcounteven.value

        r = "Results: " + str(self.resultcount.value)
        q = "Taskqueue: " + str(self.taskqueue.qsize())
        t = "Res / s : " + str(round(taskspersecond, 2))
        t2 = "Res / last s: " + str(round(taskslastsecond, 2))
        rt = "Runtime: " + str(datetime.timedelta(seconds=running))
        r = r.ljust(20)
        t = t.ljust(20)
        t2 = t2.ljust(25)
        q = q.ljust(20)
        rt = rt.ljust(20)

        if forceRaw:
            print(r + q + t + t2 + rt)
            return

        if not self.stdscr:
            print(r + q + t + t2 + rt, end="\r")
        else:
            self.stdscr.addstr(0, 0, r + q + t + t2 + rt)
            l = 1
            for k in self.timings:
                vals = self.timings[k]
                s = sum(vals)
                count = len(vals)
                avg = 0
                if count > 0:
                    avg = s / count
                self.stdscr.addstr(l, 0, k.ljust(10) + ": Avg: " + str(round(avg, 10)) + "   Count: " +str(count))
                l+=1
            self.stdscr.refresh()


    def work(self, i, worker, context):
        cancel = False
        pid = context["processid"]
        while not cancel:
            self.lock.acquire()
            try:
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
                    #self.activetasks[t["id"]] = False
            finally:
                self.lock.release()

            if len(validtasks) > 0:
                context["taskids"] = taskids
                context["trynums"] = trynums

                successes = worker(self, context, validtasks)

                for i,s in enumerate(successes):
                    tid = taskids[i]
                    self.activetasks[tid] = False
                    if not s:
                        t = validtasks[i]
                        trynum = trynums[i] + 1

                        if trynum < self.tries:
                            self.queue(t, trynum, tid)
                        else:
                            print("ERROR: " + repr(t) + " failed after " + str(trynum) + " tries")
                            self.errors.append("Task " + repr(t) + " failed with " + str(trynum) + " tries")
                    self.taskqueue.task_done()

        if self.options["timingfile"]:
            if "timing" in context:
                print("Saving timings of Process " + str(pid))
                context["timing"].saveToFile(self.options["timingfile"].replace(":pid", str(pid)))


    def getTasks(self):
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

    def getContexts(self):
        return self.contexts.copy()

    def getErrors(self):
        return self.errors

    def resultCount(self):
        return self.resultcount.value

    def queue(self, task, trynum = 0, id = None):
        self.lock.acquire()
        try:
            if id == None:
                id = self.taskid.value
                self.taskid.value += 1

            if id in self.activetasks and self.activetasks[id] == True:
                return id

            self.taskqueue.put({"t": task, "trynum": trynum, "id": id})
            self.registerTask(id, task, True)
            self.activetasks[id] = True
        finally:
            self.lock.release()

        return id

    def registerTask(self, taskid, task, locked = False):
        if not locked:
            self.lock.acquire()
        try:
            self.taskpool[taskid] = task
        finally:
            if not locked:
                self.lock.release()

    def getTaskById(self, taskid):
        self.lock.acquire()
        t = None
        try:
            if taskid in self.taskpool:
                t = self.taskpool[taskid]
        finally:
            self.lock.release()
        return t

    def result(self, keyval, val = None, context = None):
        #starttime = time.time()

        self.resultcount.value += 1
        t = math.floor(time.time())
        if t % 2 == 0:
            if self.activeresultcount.value == 1:
                self.activeresultcount.value = 0
                self.resultcounteven.value = 0
            self.resultcounteven.value += 1
        else:
            if self.activeresultcount.value == 0:
                self.activeresultcount.value = 1
                self.resultcountodd.value = 1
            self.resultcountodd.value += 1

        if not self.options["usemongo"]:
            self.lock.acquire()
            try:
                if val == None:
                    self.resultqueue.put(keyval)
                else:
                    if keyval in self.gdict:
                        print("[WARN] Duplicate Result for key " + str(keyval))
                    self.gdict[keyval] = val
            finally:
                self.lock.release()
        else:
            mongostart = time.time()
            col = self.makeMongo()
            col.insert_one({"key": keyval, "val": val})
            #print("Mongo Time: " + str(time.time() - mongostart))
        #print("Result Time: " + str(time.time() - starttime))

    def multiResult(self, valuedict, context = None):
        starttime = time.time()

        self.resultcount.value += len(valuedict)
        t = math.floor(time.time())
        if t % 2 == 0:
            if self.activeresultcount.value == 1:
                self.activeresultcount.value = 0
                self.resultcounteven.value = 0
            self.resultcounteven.value += len(valuedict)
        else:
            if self.activeresultcount.value == 0:
                self.activeresultcount.value = 1
                self.resultcountodd.value = 1
            self.resultcountodd.value += len(valuedict)

        if not self.options["usemongo"]:
            self.lock.acquire()
            try:
                for keyval,val in valuedict.items():
                    if keyval in self.gdict:
                        print("[WARN] Duplicate Result for key " + str(keyval))
                    self.gdict[keyval] = val
            finally:
                self.lock.release()
        else:
            l = []
            for keyval,val in valuedict.items():
                l.append({"key": keyval, "val": val})
            #mongostart = time.time()
            col = self.makeMongo()
            col.insert_many(l)

    def makeMongo(self, context = None):
        opts = self.options
        if context == None:
            if self.mongo != None:
                client = self.mongo
            else:
                client = pymongo.MongoClient(self.options["mongoserver"])
                self.mongo = client
        else:
            if "mongoclient" in context:
                client = context["mongoclient"]
            else:
                client = pymongo.MongoClient(self.options["mongoserver"])
                context["mongoserver"] = client
        col = client[opts["mongodb"]][opts["mongodbcol"]]
        return col

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
        return
        if self.timings.get(key, None) != None:
            self.timings[key] = self.timings[key] + [seconds]
        else:
            self.timings[key] = [seconds]
