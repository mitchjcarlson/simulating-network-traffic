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
from math import ceil
import json
import sys

## Model -----------------------------------------------------------------------


class Source(Process):
    """
    Randomly generates bursts
    """

    def generate(self, packet_params, packetDropMonitor):  # generates bursts
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
            print "%s arrived at %s" % (self.name, self.sim.now())

            # generate duration
            # Pareto distribution for burst durtion
            duration = ceil(paretovariate(packet_duration_concentration)) + min_packet_duration

            # activate burst with a duration and load balancer
            self.sim.activate(burst, burst.visit(duration, packetDropMonitor))

            i += 1


class Burst(Process):
    """
    Arrives at a random time in the future.
    Has a random, fixed duration.
    """

    def visit(self, duration, packetDropMonitor):
        print "Add %s packets to load balancer" % duration
        capacity = self.sim.load_balancer.capacity
        amount = self.sim.load_balancer.amount
        sendPackets = capacity-amount

        if duration > sendPackets:
            droppedPackets = duration-sendPackets
            yield put, self, self.sim.load_balancer, sendPackets  # offer a duration to load_balancer
            self.sim.burst_duration_monitor.observe(sendPackets)
            packetDropMonitor.observe(droppedPackets)
        else:
            yield put, self, self.sim.load_balancer, duration  # offer a duration to load_balancer
            self.sim.burst_duration_monitor.observe(duration)


class Host(Process):
    """
    Processes packets in load balancer.
    """

    def process(self, num_packets):
        while True:
            # pull packets from load balancer
            yield get, self, self.sim.load_balancer, num_packets
            print "[%s]: Process %s packets in load balancer at %s" % (self.name, num_packets, self.sim.now())
            # generate service time
            process_time = num_packets
            # stay busy until service time expires
            yield hold, self, process_time


class Model(Simulation):

    def __init__(self, name, packet_params, load_balancer_capacity, host_params):
        super(Model, self).__init__()
        self.name = name
        self.packet_params = packet_params
        self.load_balancer_capacity = load_balancer_capacity
        self.host_params = host_params
        return

    def runModel(self, start_time, end_time, packetDropMonitor):
        # monitor the burst duration
        self.burst_duration_monitor = Monitor(name='Pareto distribution', sim=self)
        self.initialize()

        # Represents queue in load balancer
        self.load_balancer = Level(name='load_balancer', unitName='packet',
                                   capacity=self.load_balancer_capacity,
                                   initialBuffered=0,
                                   putQType=FIFO, getQType=FIFO,
                                   monitored=False, monitorType=Monitor,
                                   sim=self)
        burst_source = Source(name='Source', sim=self)
        self.activate(burst_source,
                      burst_source.generate(self.packet_params,packetDropMonitor=packetDropMonitor),
                      at=start_time)  # priority is now

        for i in xrange(self.host_params["count"]):
            host = Host(name="Host %s" % i, sim=self)
            self.activate(host, host.process(self.host_params["capacity"]))

        self.simulate(until=end_time)

        # print burst statistics
        for i in xrange(len(self.burst_duration_monitor)):
            print 'Duration {}'.format(self.burst_duration_monitor[i])

        result = self.burst_duration_monitor.count(), self.burst_duration_monitor.mean()
        print("Average duration of %3d bursts was %5.3f milliseconds." % result)
        print(packetDropMonitor.total())


def main():
    if len(sys.argv) < 3:
        print "usage: {0} <experiment-name> <parameter file>".format(sys.argv[0])
        sys.exit("Must specifiy parameter file!")

    ## Experiment data ---------------------------------------------------------
    packetDropMonitor = Monitor()
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
        myModel.runModel(time["start"], time["end"],packetDropMonitor)
        print myModel.now()

    ## Analysis ----------------------------------------------------------------

    ## Output ------------------------------------------------------------------


if __name__ == '__main__':
    main()
