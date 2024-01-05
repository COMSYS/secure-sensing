import time
import threading, multiprocessing
import math, statistics
import numpy as np
import scipy.stats
from gclasses import fileutils

class Timer:
    def __init__(self, threadsafe = True, mp = False, mpdisable = False):
        self.timings = {}
        self.history = []
        self.mp = mp
        self.disable = False
        self.threadsafe = threadsafe or (mp and not mpdisable)
        if mp:
            self.disable = True
            self.lock = multiprocessing.Lock()
            self.m = multiprocessing.Manager()
            self.timings = self.m.dict()
            self.history = self.m.list()
        elif threadsafe:            
            self.lock = threading.Lock()
        self.metadata = {}
        
    def combine(self, other, prefix = False, dropfirst = []):
        """
        Combines timings from the current instance with the timings of another instance or just the timing object
        If prefix is a string, all keys of the measurements of the other timing will be prefixed with given string
        """
        if type(other) == dict:
            t = other
        else:
            t = other.timings
        for k in t:
            nk = k
            if prefix != False:
                nk = prefix + k
            measures = t[k]
            if k in dropfirst and len(measures) > 0:
                measures = measures[1:]

            if not nk in self.timings:
                self.timings[nk] = measures
            else:
                self.timings[nk].extend(measures)
    
    def dropFirst(self, key):
        if not key in self.timings:
            return True
        self.timings[key] = self.timings[key][1:]

    def saveToFile(self, file):
        obj = {
            "timings": self.timings,
            "history": self.history,
            "metadata": self.metadata
        }
        return fileutils.file_put_contents(file, obj)
        
    def loadFromFile(self, file):
        obj = fileutils.file_get_contents(file, True)
        if type(obj) == dict:
            self.timings = obj["timings"]
            self.history = obj["history"]
            self.metadata = obj["metadata"]
            return True
        return False
        
    def start(self, name, skiphistory = False):        
        if self.disable:
            return 0
        if self.threadsafe:
            self.lock.acquire()
        #if name in self.timings and not self.timings[name][-1]["ended"]:
        #    self.lock.release()
        #    raise ValueError("Measurement of " + name + " currently active")            
           
        id = None
        try:
            if not name in self.timings:
                if self.mp:
                    self.timings[name] = self.m.list()
                else:
                    self.timings[name] = []
            
            self.timings[name].append({
                "name": name,
                "ended": False,
                "starttime": time.time(),
                "endtime": False,
                "duration": False,
                "endid": 0,
                "skipprint": skiphistory
            })
            if not skiphistory:
                self.history.append("START   " + name)
            id = len(self.timings[name])
        finally:
            if self.threadsafe:
                self.lock.release()
        return id - 1
        
    def stop(self, name, skiphistory = False, id = -1):
        if self.disable:
            return 0
        if self.threadsafe:
            self.lock.acquire()
            
        if not name in self.timings:
            if self.threadsafe:
                self.lock.release()
            raise ValueError("Measurement of " + name + " has to be started first")
        
        try:
            if self.timings[name][id]["ended"]:
                raise ValueError("Measurement of " + name + " already ended")
                                    
            self.timings[name][id]["ended"] = True
            self.timings[name][id]["endtime"] = time.time()
            self.timings[name][id]["duration"] = self.timings[name][id]["endtime"] - self.timings[name][id]["starttime"]
            
            if not skiphistory:
                self.history.append("STOP    " + name.ljust(30) + " " + str(self.timings[name][id]["duration"]) + "s")
        finally:
            if self.threadsafe:
                self.lock.release()
        return True
        
    def timing(self, name, duration):
        if self.threadsafe:
            self.lock.acquire()
            
        try:
            if not name in self.timings:
                self.timings[name] = []
                
            now = time.time()
            self.timings[name].append({
                "name": name,
                "ended": True,
                "starttime": now - duration,
                "endtime": now,
                "duration": duration,
                "endid": 0,
                "skipprint": True
            })
            
        finally:
            if self.threadsafe:
                self.lock.release()
        return True
       
    
    def getObj(self):
        return self.timings
        
    def getHistory(self, sortByEnd=False):            
        return self.history
        
    def getStats(self, sortkey="endid"):
        events = []
        for k,l in self.timings.items():
            events.extend(l)
            
        s = sorted(events, key=lambda x: x[sortkey])
        stats = []
                
        for i in s:
            if not i["skipprint"]:
                stats.append(i["name"].ljust(30) + " " + str(i["duration"]) + " s")
        return stats, s
        
    def getMeanConfidenceInterval(self, name, confidence=0.95):
        data = self.getSorted(name, "duration")
        a = 1.0 * np.array(data)
        n = len(a)
        m = np.mean(a)
        if n <= 1:
            return m, m, m
            
        se = scipy.stats.sem(a)
        
        interval = scipy.stats.t.interval(confidence, n-1, loc=m, scale=se)
        return interval[0], m, interval[1]
            
        h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
        low = m-h
        high = m+h
        if math.isnan(low):
            low = m
        if math.isnan(high):
            high = m    
        return low, m, high
        
    def getHistogram(self, name, bins=1000):
        a = self.getSorted(name, "duration")
        hist = np.histogram(a, bins)
        return hist
        
        
    def getPredictionInterval(self, name, confidence=0.95):    
        data = self.getSorted(name, "duration")
        a = 1.0 * np.array(data)
        n = len(a)
        mu = np.mean(a)
                     
        sigma = self.getStdev(name)
        
        clow = (1 - confidence) / 2
        chigh = confidence + clow
        
        qlow = self.getQuantile(name, clow)        
        qhigh = self.getQuantile(name, chigh)
        
        # zlow = (qlow - mu) / sigma
        # zhigh = (qhigh + mu) / sigma
                
        # # l = mu - qlow * sigma
        # # h = mu + qhigh * sigma
        # l = mu - zlow * sigma
        # h = mu + zhigh * sigma
        
        return qlow,qhigh
        
    def getMax(self, name):
        if not name in self.timings:
            return 0
        m = 0
        for t in self.timings[name]:
            m = max(m, t["duration"])
        return m
            
    def getMin(self, name):
        if not name in self.timings:
            return 0
        m = None
        for t in self.timings[name]:
            if m == None:
                m = t["duration"]
            else:
                m = min(m, t["duration"])
        return m
            
    def getAvg(self, name):
        if not name in self.timings:
            return 0
        sum = 0
        
        a = 1.0 * np.array(list(map(lambda x: x["duration"], self.timings[name])))
        n = len(a)
        m = np.mean(a)
        
        return float(m)
        
    def getSum(self, name):
        if not name in self.timings:
            return 0
        sum = 0
        for t in self.timings[name]:
            sum += t["duration"]
        return sum
        
    def getCount(self, name):
        if not name in self.timings:
            return 0
        return len(self.timings[name])
        
    def getSorted(self, name, key=None):
        if not name in self.timings:
            return []
            
        t = self.timings[name]
        s = sorted(t, key=lambda x: x["duration"])
        if key == None:
            return s
        return list(map(lambda x: x[key], s))
        
    def getQuantile(self, name, p):
        if p <= 0 or p >= 1:
            raise ValueError("Invalid Quantile requested: " + str(p))
            
        s = self.getSorted(name)
                
        n = len(s)
        m = n*p - 1
        if m.is_integer():
            m = int(m)
            xp = 0.5*(s[m]["duration"] + s[m+1]["duration"])
        else:
            xp = s[math.floor(m+1)]["duration"]
            
        return xp
        
    def get2ndMax(self, name):
        m = None
        s = self.getSorted(name, "duration")
        if len(s) > 1:
            return s[-2]
        return m
    
    def get2ndMin(self, name):
        m = None
        s = self.getSorted(name, "duration")
        if len(s) > 1:
            return s[1]
        return m
        
    def getMedian(self, name):
        return self.getQuantile(name, 0.5)
       
    def getStdev(self, name):
        vals = self.getSorted(name, "duration")
        if len(vals) <= 1:
            return None
        return statistics.stdev(vals)
        
    def getVariance(self, name):
        vals = self.getSorted(name, "duration")
        if len(vals) <= 1:
            return None
        return statistics.variance(vals)
        
    def translateKeys(self):
        translate = {
            "count": "Count",
            "total": "Sum",
            "max": "Maximum",
            "2ndmax": "2nd highest Value",
            "min": "Minimum",
            "2ndmin": "2nd lowest Value",
            "mean": "Mean / Average",
            "cint95": "Confidence Mean 95%",
            "pint95": "Prediction Interval 95%",
            "cint99": "Confidence Mean 99%",
            "pint99": "Prediction Interval 99%",
            "stddev": "Standard Deviation",
            "relstddev": "Relative StdDev (%)",
            "var": "Variance",
            "median": "Median",
            "histogram": "Histogram"
        }
        for p in [0.01, 0.05, 1/4, 1/3, 2/3, 3/4, 0.95, 0.99]:
            q = "{:.3f}".format(p)
            translate["quantile-" + q] = q + " Quantile"
            
        return translate
        
    def getFullStats(self, name):    
        if not name in self.timings:
            return False
        
        d = {}
        d["count"] = self.getCount(name)
        d["total"] = self.getSum(name)
        d["max"] = self.getMax(name)
        d["2ndmax"] = self.get2ndMax(name)
        d["min"] = self.getMin(name)
        d["2ndmin"] = self.get2ndMin(name)
        d["mean"] = self.getAvg(name)
        clow, _, chigh = self.getMeanConfidenceInterval(name)
        plow, phigh = self.getPredictionInterval(name)
        d["cint95"] = [clow, chigh]
        d["pint95"] = [plow, phigh]
        clow, _, chigh = self.getMeanConfidenceInterval(name,confidence=0.99)
        plow, phigh = self.getPredictionInterval(name,confidence=0.99)
        d["cint99"] = [clow, chigh]
        d["pint99"] = [plow, phigh]
        d["stddev"] = self.getStdev(name)   
        h, b = self.getHistogram(name)   
        d["histogram"] = h
        d["bins"] = b
        
        
        try:
            relstddev = 100 * d["stddev"] / d["mean"]
        except Exception:
            relstddev = None
        d["relstddev"] = relstddev
        d["var"] = self.getVariance(name)
        d["median"] = self.getMedian(name)
        for p in [0.01, 0.05, 1/4, 1/3, 2/3, 3/4, 0.95, 0.99]:
            q = "{:.3f}".format(p)
            d["quantile-" + q] = self.getQuantile(name, p)
        
        return d
        
    def printFullStats(self, name, title = None):
        if title == None:
            title = name
    
        if not name in self.timings:
            return "No Measurement saved"
        
        d = {}
        d["Count"] = self.getCount(name)
        d["Total"] = self.getSum(name)
        d["Max"] = self.getMax(name)
        d["Min"] = self.getMin(name)
        d["Average"] = self.getAvg(name)
        clow, _, chigh = self.getMeanConfidenceInterval(name)
        d["Confidence Mean 95%"] = [clow, chigh]
        clow, _, chigh = self.getMeanConfidenceInterval(name,confidence=0.99)
        d["Confidence Mean 99%"] = [clow, chigh]
        d["Std Deviation"] = self.getStdev(name)
        d["Variance"] = self.getVariance(name)
        d["Median"] = self.getMedian(name)
        for p in [0.05, 1/4, 1/3, 2/3, 3/4, 0.95]:
            q = "{:.3f}".format(p)
            d[q + " Quantile"] = self.getQuantile(name, p)
        
        print("== " + title + " (" + name + ")")
        for k,v in d.items():
            print("  " + k.rjust(20) + ":  " + str(v).ljust(10))
        print("")
