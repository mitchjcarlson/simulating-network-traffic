#-------------------------------------------------------------------------------
# Name:        <filename.py>
# Scenario:    <describe scenario for simulation>
#
# Model:       <describe model>

# Author:      <your name>
#
# Created:     <yyyy-mm-dd>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

## Model components ------------------------------------------------------------
from SimPy.Simulation import *

## Model -----------------------------------------------------------------------


class Source(Process):
    """
    Randomly generates bursts
    """
    def generate(self):
        return


class Burst(Process):
    """
    Arrives at a random time in the future.
    Has a random, fixed duration.
    """

    def visit(self, length):
        return


class Host(Process):
    """
    Processes packets in load balancer.
    """


class Model(Simulation):

    def __init__(self, name):
        self.name = name
        self.load_balancer_capacity = 1
        return

    def runModel(self):

        # Represents queue in load balancer
        load_balancer = Level(name='load_balancer', unitName='packet',
            capacity=self.load_balancer_capacity, initialBuffered=0,
            putQType=FIFO, getQType=FIFO,
            monitored=False, monitorType=Monitor)
        return

def main():

    ## Experiment data ---------------------------------------------------------

    ## Experiment --------------------------------------------------------------

    myModel = Model(name="Experiment 1")
    myModel.runModel()
    print myModel.now()

    ## Analysis ----------------------------------------------------------------

    ## Output ------------------------------------------------------------------


if __name__ == '__main__':
    main()