""" Example Hello World plugin """
from supremm.plugin import Plugin
from supremm.errors import ProcessingError
import numpy as np
import math
import operator

class HelloWorld(Plugin):
    """ Example implementation of a plugin """

    # The name property is required and is used to uniquely identify
    # this plugin in the output
    name = property(lambda x: "helloworld")

    # The mode defines what data will be passed to the plugin.
    # A mode of 'all' means every datapoint for the job
    # A mode of 'firstlast' means just the first and final measurement.
    mode = property(lambda x: "all")

    # the plugin will only be run if all required metrics are
    # present in the data. However, multiple sets of metrics
    # may be specified.
    requiredMetrics = property(lambda x: [["kernel.percpu.cpu.user"]])

    # if optional metrics are available then they will be loaded, but
    # their absence will not prevent the plugin from running
    optionalMetrics = property(lambda x: [])

    # derived metrics are deprecated
    derivedMetrics = property(lambda x: [])

    def __init__(self, job):
        super(HelloWorld, self).__init__(job)
        self._CPUcounter = 0
        self._TimestampsCounter = 0
        self._Outliers = {}
        self._timestamps = []
        self._GoodPerformers = set()
        self._last = {}
        self._usagePercent = {}

    def findMedian(self, ListTuples):
        Length = len(ListTuples)
        median = 0
        if Length == 0: #if even
            upper = (Length/2)+1
            median = (Length/2 + upper) / 2
        else: #if odd
            median = Length/2
        return median

    # The process function get called for every requested timestep
    # for every compute node on which the job ran
    def process(self, nodemeta, timestamp, data, description):
        #nodemeta is info about compute node
        NodeName = (nodemeta.nodename)
        self._CPUcounter = len(data[0])
        processTime = 0
        if self._last.get(NodeName) is None:
            self._timestamps.append(timestamp)
            self._timestamps.append(timestamp)
            self._last[NodeName] = data[0]
            self._Outliers[NodeName] = set()
            self._usagePercent[NodeName] = []
            self._TimestampsCounter += 1
            return True
        processTime = timestamp - self._timestamps[1]
        rateCPUs = {}
        for val in range(0, self._CPUcounter):
            useTimeEachCPU = (data[0][val] - self._last[NodeName][val]) / 1000
            rateOfChange = (useTimeEachCPU / processTime) * 100
            rateCPUs[val] = rateOfChange
        rateCPUs = sorted(rateCPUs.items(), key=operator.itemgetter(1)) #rateCPUs is list of tuple
        #find median,q1,q3
        median = self.findMedian(rateCPUs)
        firstHalf = rateCPUs[:int(math.floor(median))]
        secondHalf = rateCPUs[int(math.ceil(median)):]
        Q1 = self.findMedian(firstHalf)
        Q3 = self.findMedian(secondHalf)
        #find IQR
        IQR = rateCPUs[Q3][1] - rateCPUs[Q1][1]
        #find _Outliers
        for val in range(0, self._CPUcounter):
            if (rateCPUs[val][1] < (rateCPUs[Q1][1] - (5*IQR))) or (rateCPUs[val][1] > (rateCPUs[Q3][1] + (5*IQR))):
                self._Outliers[NodeName].add(val)
            else:
                self._GoodPerformers.add(val)
        self._usagePercent[NodeName].append(rateCPUs)
        self._timestamps[1] = timestamp
        self._TimestampsCounter += 1
        self._last.update({NodeName : data[0]})
        return True

    # The results function is called once after all available data
    # has been passed to the process function. It should return a
    # dictionary containing the results of the data analysis
    def results(self):
        if self._CPUcounter <= 1:
            return {"error": ProcessingError.INSUFFICIENT_DATA}
        improperBehavior = set()
        for node in self._Outliers:
            improperBehavior = self._Outliers[node] - self._GoodPerformers
        return {"CPUs exhibit improper behavior: ": improperBehavior, "Number of Outliers: " : len(self._Outliers) , "Outliers: " : self._Outliers}
