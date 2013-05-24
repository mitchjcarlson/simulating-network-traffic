#-------------------------------------------------------------------------------
# Name:        simulation.py
# Scenario:    Modeling network traffic to a group of hosts and a load balancer.
#
# Model:       Uses a Poisson-Pareto burst process with a single queue and
#              multiple servers

# Author:      Brendan Sweeny, Derek McLean, Mitch Carlson
#
# Created:     2013-05-13
#-------------------------------------------------------------------------------

#!/usr/bin/env python

## Model components ------------------------------------------------------------
from SimPy.Simulation import *
from random import expovariate, paretovariate, seed
from math import ceil, sqrt
import json
import sys

## Model -----------------------------------------------------------------------


class Source(Process):
    """
    Randomly generates bursts
    """

    def generate(self, packet_params):  # generates bursts
        meanTBA = packet_params["mean-arrival"]
        min_packet_duration = packet_params["min-duration"]
        packet_duration_concentration = packet_params["duration-concentration"]

        i = 0
        while True:
            # initialize burst at random time in future with random duration
            burst = Burst(name="Burst %s" % i, sim=self.sim)

            # generate next burst time
            # yield to next burst time
            # arrival time of burst a Poisson distr
            interarrival_time = expovariate(1.0 / meanTBA)
            yield hold, self, interarrival_time  # hold suspends until interarrival time has passed

            # generate duration
            # Pareto distribution for burst durtion
            duration = ceil(paretovariate(packet_duration_concentration)) + min_packet_duration
            print "%s arrived at %s w/ duration = %s" % (self.name, self.sim.now(), duration)

            # activate burst with a duration and load balancer
            self.sim.activate(burst, burst.visit(duration))

            i += 1


class Burst(Process):
    """
    Arrives at a random time in the future.
    Has a random, fixed duration.
    """

    def visit(self, duration):
        #print "Add %s packets to load balancer" % duration
        capacity = self.sim.load_balancer.capacity
        amount = self.sim.load_balancer.amount
        sendPackets = capacity-amount

        if duration > sendPackets:
            droppedPackets = duration-sendPackets
            yield put, self, self.sim.load_balancer, sendPackets  # offer a duration to load_balancer
            self.sim.burst_duration_monitor.observe(sendPackets)
            self.sim.packetDropMonitor.observe(droppedPackets)
        else:
            yield put, self, self.sim.load_balancer, duration  # offer a duration to load_balancer
            self.sim.burst_duration_monitor.observe(duration)

        self.sim.PacketArrived.signal()


class Host(Process):
    """
    Processes packets in load balancer.
    """

    def process(self, max_capacity):
        while True:
            if self.sim.load_balancer.amount < 1:
                start = self.sim.now()
                yield waitevent, self, self.sim.PacketArrived
                self.sim.host_monitor.observe(self.sim.now() - start)
            else:
                num_packets = max_capacity
                if self.sim.load_balancer.amount < max_capacity:
                    num_packets = self.sim.load_balancer.amount

                # pull packets from load balancer
                yield get, self, self.sim.load_balancer, num_packets
                print "[%s]: Process %s packets in load balancer at %s" % (self.name, num_packets, self.sim.now())
                # stay busy until service time expires
                yield hold, self, 1


class Model(Simulation):

    def __init__(self, name, packet_params, load_balancer_capacity, host_params):
        super(Model, self).__init__()
        self.name = name
        self.packet_params = packet_params
        self.load_balancer_capacity = load_balancer_capacity
        self.host_params = host_params
        return

    def runModel(self, start_time, end_time):
        # monitor the burst duration
        self.burst_duration_monitor = Monitor(name="Bursts", sim=self)
        self.packetDropMonitor = Monitor(name="Packet Drop", sim=self)
        self.host_monitor = Monitor(name="Host", sim=self)

        self.PacketArrived = SimEvent(name="Packet Arrived", sim=self)

        self.initialize()

        # Represents queue in load balancer
        self.load_balancer = Level(name='load_balancer', unitName='packet',
                                   capacity=self.load_balancer_capacity,
                                   initialBuffered=0,
                                   putQType=FIFO, getQType=FIFO,
                                   monitored=True, monitorType=Monitor,
                                   sim=self)
        burst_source = Source(name='Source', sim=self)
        self.activate(burst_source,
                      burst_source.generate(self.packet_params),
                      at=start_time)  # priority is now

        for i in xrange(self.host_params["count"]):
            host = Host(name="Host %s" % i, sim=self)
            self.activate(host, host.process(self.host_params["max-capacity"]))

        self.simulate(until=end_time)

        return self.burst_duration_monitor, self.packetDropMonitor, self.load_balancer.bufferMon, self.host_monitor


def dump_monitor(monitor, testname, monitorname):
    with open("{0}-{1}-stats.out".format(testname, monitorname), "wb") as fd:
        fd.write("observations = %3d\n" % monitor.count())
        fd.write("total = %3d\n" % monitor.total())
        if monitor.count() is 0:
            fd.write("mean = 0\n")
            fd.write("var = 0\n")
            fd.write("stddev = 0\n")
        else:
            fd.write("mean = %5.3f\n" % monitor.mean())
            fd.write("var = %5.3f\n" % monitor.var())
            fd.write("stddev = %5.3f\n" % sqrt(monitor.var()))
        fd.write("time-mean = %5.3f\n" % (monitor.timeAverage() or float(0.0)))

    with open("{0}-{1}-data.out".format(testname, monitorname), "wb") as fd:
        fd.write("t,length\n")
        for data in monitor:
            fd.write("{0}\n".format(",".join(map(str, data))))


def main():
    if len(sys.argv) < 3:
        print "usage: {0} <experiment-name> <parameter file>".format(sys.argv[0])
        sys.exit("Must specifiy experiment name and parameter file!")

    ## Experiment data ---------------------------------------------------------
    name = sys.argv[1]
    with open(sys.argv[2]) as parameter_file:
        params = json.load(parameter_file)
        time = params["time"]

    ## Experiment -------------------------------------------------------------
        if params["seed"]:
            seed(params["seed"])

        myModel = Model(name=name,
                        packet_params=params["packet"],
                        load_balancer_capacity=params["load-balancer-capacity"],
                        host_params=params["host"])
        burst_monitor, packet_drop_monitor, load_balancer_monitor, server_monitor = myModel.runModel(time["start"], time["end"])

    ## Analysis ----------------------------------------------------------------

    ## Output ------------------------------------------------------------------
    dump_monitor(burst_monitor, name, "burst")
    dump_monitor(packet_drop_monitor, name, "packetdrop")
    dump_monitor(load_balancer_monitor, name, "loadbalancer")
    dump_monitor(server_monitor, name, "serverutilization")

if __name__ == '__main__':
    main()
