import events
from collections import deque

class Customer(object):

    def __init__(self):
        self.arrival_time = 0
        self.wait_start = 0
        self.wait_end = 0
        self.service_start = 0
        self.service_end = 0
        self.balked = False

    @property
    def wait_time(self):
        return self.wait_end - self.wait_start

    @property
    def service_time(self):
        return self.service_end - self.service_start

    @property
    def total_time(self):
        return self.wait_time + self.service_time

    def __str__(self):
        return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            self.arrival_time,
            self.wait_start,
            self.wait_end,
            self.wait_time,
            self.service_start,
            self.service_end,
            self.service_time,
            self.total_time,
            ["no","yes"][self.balked]
        )

    @staticmethod
    def str_header():
        return "arrival_time\twait_start\twait_end\twait_time\tservice_start\tservice_end\tservice_time\ttotal_time\tbalked?"

class Server(object):

    def __init__(self, service_rng):
        self.service_rng = service_rng
        self.state = False

    def serve(self, time, customer):
        self.state = True
        customer.service_start = time
        return FinishService(time + next(self.service_rng), customer, self)


class System(object):

    def __init__(self, queue_size, servers):
        self.queue = deque([], queue_size)
        self.servers = servers

    def get_idle_server(self):
        for server in self.servers:
            if not server.state:
                return server
        return None

    def wait_customer(self, customer, time):
        if len(self.queue) is self.queue.maxlen:
            return False
        else:
            customer.wait_start = time
            self.queue.append(customer)
            return True

    def get_waiting_customer(self, time):
        if len(self.queue) is self.queue.maxlen:
            customer = self.queue.popleft()
            customer.wait_end = time
            return customer
        return None

class Arrival(events.Event):

    def handle(self, state):
        self.customer.arrival_time = self.time
        server = state.get_idle_server()
        if server:
            return server.serve(self.time, self.customer)
        else:
            if not state.wait_customer(self.customer, self.time):
                self.customer.balked = True
            return None

class FinishService(events.Event):
    
    def __init__(self, time, customer, server):
        super(FinishService,self).__init__(time, customer)
        self.server = server

    def handle(self, state):
        self.customer.service_end = self.time
        waiting_customer = state.get_waiting_customer(self.time)
        if waiting_customer:
            return self.server.serve(self.time, waiting_customer)
        else:
            self.server.state = False
            return None