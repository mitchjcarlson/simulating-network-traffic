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

## Model -----------------------------------------------------------------------


class Source(Process):
    """
    Randomly generates bursts
    """

    def generate(self, meanTBA, min_packet_duration, packet_duration_shape):  # generates bursts
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
            duration = ceil(paretovariate(packet_duration_shape)) + min_packet_duration

            # activate burst with a duration and load balancer
            self.sim.activate(burst, burst.visit(duration))

            i += 1


class Burst(Process):
    """
    Arrives at a random time in the future.
    Has a random, fixed duration.
    """

    def visit(self, duration):
        print "Add %s packets to load balancer" % duration
        # start duration timer
        burst = now()

        yield put, self, self.sim.load_balancer, duration  # offer a duration to load_balancer

        self.sim.burst_duration_monitor.observe(duration)
        # end duration timer
        # duration = now() - burst  # time passed durring burst
        # record duration


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

    def __init__(self,
                 name,
                 mean_packet_arrival,
                 min_packet_duration,
                 packet_duration_shape,
                 load_balancer_capacity,
                 number_hosts,
                 host_process_capacity):
        super(Model, self).__init__()
        self.name = name
        self.mean_packet_arrival = mean_packet_arrival
        self.load_balancer_capacity = load_balancer_capacity
        self.number_hosts = number_hosts
        self.host_process_capacity = host_process_capacity
        return

    def runModel(self, start_time, end_time):
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
                      burst_source.generate(meanTBA=self.mean_packet_arrival,
                                            min_packet_duration=min_packet_duration,
                                            packet_duration_shape=packet_duration_shape),
                      at=start_time)  # priority is now

        for i in xrange(self.number_hosts):
            host = Host(name="Host %s" % i, sim=self)
            self.activate(host, host.process(self.host_process_capacity))

        self.simulate(until=end_time)

        # print burst statistics
        for i in xrange(len(self.burst_duration_monitor)):
            print 'Duration {}'.format(self.burst_duration_monitor[i])

        result = self.burst_duration_monitor.count(), self.burst_duration_monitor.mean()
        print("Average duration of %3d bursts was %5.3f milliseconds." % result)

## Experiment data ---------------------------------------------------------

mean_packet_arrival = 100   # average interarrival time of 100 milliseconds
min_packet_duration = 40
packet_duration_shape = 1.0

load_balancer_capacity = 'unbounded'
number_hosts = 20
host_process_capacity = 150

start_time = 0.0
end_time = 3600000  #86400000  # number of milliseconds in a day


def main():
    ## Experiment --------------------------------------------------------------
    seed(9999)

    myModel = Model(name="Experiment 1",
                    mean_packet_arrival=mean_packet_arrival,
                    min_packet_duration=min_packet_duration,
                    packet_duration_shape=packet_duration_shape,
                    load_balancer_capacity=load_balancer_capacity,
                    number_hosts=number_hosts,
                    host_process_capacity=host_process_capacity)
    myModel.runModel(start_time, end_time)
    print myModel.now()

    ## Analysis ----------------------------------------------------------------

    ## Output ------------------------------------------------------------------


if __name__ == '__main__':
    main()
