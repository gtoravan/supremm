""" CPU pin tracker plugin """
from supremm.plugin import Plugin
from supremm.errors import ProcessingError

class PinTrackerPrototype(Plugin):
    # The name property is required and is used to uniquely identify
    # this plugin in the output
    name = property(lambda x: "PinTrackerPrototype")

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
        super(PinTrackerPrototype, self).__init__(job)
        self._CPUcounter = 0
        self._ProcessCounter = 0
        self._PinnedTracker = []
        self._firstdata = []
        self._lastdata = []
        self._timestamps = []
        self._ProcessTimes = []
        self._history = []


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
        self._history.append(data[0])
        processTime = timestamp - self._timestamps[1]
        self._ProcessTimes.append(processTime)
        self._timestamps[1] = timestamp
        self._ProcessCounter += 1
        return True

    # The results function is called once after all available data
    # has been passed to the process function. It should return a
    # dictionary containing the results of the data analysis
    def results(self):
        usePercentage = []
        avgUSEtime = []
        if self._CPUcounter == 1:
            return {"Average use Time": self._data}
        totalProcessTime = (self._timestamps[1] - self._timestamps[0])
        for pro in range(1, self._ProcessCounter):
            processTime = self._ProcessTimes[pro]
            eachProcess = []
            for val in range(0, self._CPUcounter):
                useTimeEachCPU = (self._history[pro][val] - self._history[pro - 1][val]) / 1000
                # print "CPUTIme {}".format(useTimeEachCPU)
                rateOfChange = useTimeEachCPU / processTime
                if ((rateOfChange * 100)) > 5:
                    self._PinnedTracker.append(val)
                eachProcess.append(rateOfChange * 100)
            usePercentage.append(eachProcess)
        for cpu in range(0, self._CPUcounter):
            usetotaltimeCPU = (self._lastdata[cpu] - self._firstdata[cpu]) / 1000
            avgCPUusetime = usetotaltimeCPU / totalProcessTime * 100
            avgUSEtime.append(avgCPUusetime)
        self._PinnedTracker = list(set(self._PinnedTracker))
        return {"avg CPU use time:" : avgUSEtime , "total CPUs:" : self._CPUcounter , "CPUs utilization greater than 5%: " : len(self._PinnedTracker) , "pin tracker: " : self._PinnedTracker}
