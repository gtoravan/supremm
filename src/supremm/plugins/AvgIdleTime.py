d""" Example Avg Idle time plugin """
from supremm.plugin import Plugin
from supremm.errors import ProcessingError
import numpy

class AvgIdleTime(Plugin):
    """ Example implementation of a plugin """

    # The name property is required and is used to uniquely identify
    # this plugin in the output
    name = property(lambda x: "AvgIdleTime")

    # The mode defines what data will be passed to the plugin.
    # A mode of 'all' means every datapoint for the job
    # A mode of 'firstlast' means just the first and final measurement.
    mode = property(lambda x: "all")

    # the plugin will only be run if all required metrics are
    # present in the data. However, multiple sets of metrics
    # may be specified.
    requiredMetrics = property(lambda x: [["kernel.percpu.cpu.idle"]])

    # if optional metrics are available then they will be loaded, but
    # their absence will not prevent the plugin from running
    optionalMetrics = property(lambda x: [])

    # derived metrics are deprecated
    derivedMetrics = property(lambda x: [])

    def __init__(self, job):
        super(HelloWorld, self).__init__(job)
        self._firstdata = []
        self._lastdata = []
        self._timestamps = []
        self._CPUcounter = 0
        self._IdleCPU = []
        self._ProcessCounter = 0
        self._ProcessTimes = []

    # The process function get called for every requested timestep
    # for every compute node on which the job ran
    def process(self, nodemeta, timestamp, data, description):
        self._CPUcounter = len(data[0])
        processTime = 0
        if self._ProcessCounter == 0:
            self._timestamps.append(timestamp)
            self._timestamps.append(timestamp)
            self._firstdata = data[0]
            self._lastdata = data[0]
        else:
            self._lastdata = data[0]
        processTime = timestamp - self._timestamps[1]
        self._ProcessTimes.append(processTime)
        self._timestamps[1] = timestamp
        self._ProcessCounter += 1
        # return True
        print "first is {} and last is {} Processing at time {} for node {} (desc {})".format(self._firstdata, self._lastdata , timestamp, nodemeta.nodename, description)

    # The results function is called once after all available data
    # has been passed to the process function. It should return a
    # dictionary containing the results of the data analysis
    def results(self):
        percentIdle = []
        #avg cpu idle time = sum of each process idle time / number of processes ran
        if self._CPUcounter == 1:
            return {"Average Idle Time": self._data}
        totalProcessTime = (self._timestamps[1] - self._timestamps[0])
        for val in range(0, self._CPUcounter):
            idletime = (self._lastdata[val] - self._firstdata[val]) / 1000
            self._IdleCPU.append( (idletime) / self._ProcessCounter)
            percentIdle.append( (idletime / (totalProcessTime) * 100))   #percent idle time = sum idle time / total time(secs to jiffies)
        AverageIdlePercent = sum(percentIdle) / self._CPUcounter
        return {"Average Idle Percentage for Job :": AverageIdlePercent,  "timestamps- ": self._timestamps, "total process time secs: ": totalProcessTime , "Average Idle Time per process in jiffy": self._IdleCPU , "Percent of Idle time for every CPU" : percentIdle , "Number of Processes" : self._ProcessCounter}
