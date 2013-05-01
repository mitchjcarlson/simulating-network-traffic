import rng
import events
from Queue import Queue

class System(object):

    def __init__(self, queue_size, server_busy = False):
        self.queue = Queue(maxsize = queue_size)
        self.server_busy = server_busy

class Customer(object):

    def __init__(self, id):
        self.id = id
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
        return "%s\t%s\t%s\t%s\t%s\t%s" % (self.id, self.arrival_time, self.wait_time, self.service_time, self.total_time, self.balked)

    @staticmethod
    def str_header():
        return "id\tarrival_time\twait_time\tservice_time\ttotal_time\tbalked?"

class Arrival(events.RandomEvent):

    def handle(self, state):
        self.customer.arrival_time = self.time
        if state.server_busy:
            if state.queue.empty():
                state.queue.put(self.customer)
                self.customer.wait_start = self.time
            else:
                self.customer.balked = True
        else:
            state.server_busy = True
            self.customer.service_start = self.time
            return FinishService.random(self.time, self.customer)

class FinishService(events.RandomEvent):

    def handle(self, state):
        self.customer.service_end = self.time
        if state.queue.full():
            customer = state.queue.get()
            customer.wait_end = self.time
            customer.service_start = self.time
            return FinishService.random(self.time, customer)
        else:
            state.server_busy = False
            return None

def main():
    arrival_emp_prob = [
         (0, 0.09),
         (1, 0.17),
         (2, 0.27),
         (3 ,0.20),
         (4, 0.15),
         (5, 0.12)
    ]

    service_emp_prob = [
         (1, 0.20),
         (2, 0.40),
         (3 ,0.28),
         (4, 0.12)
    ]

    Arrival.rng = rng.emperical_rng(rng.cumulative_emperical(arrival_emp_prob))
    FinishService.rng = rng.emperical_rng(rng.cumulative_emperical(service_emp_prob))

    customers = [Customer(i) for i in xrange(1,11)]

    future_events_list = events.EventList()
    arrival_time = 0
    for customer in customers:
        arrive_event = Arrival.random(arrival_time, customer)
        arrival_time = arrive_event.time
        future_events_list.push(arrive_event)

    customers.insert(0, Customer(0))
    future_events_list.push(FinishService(3, customers[0]))
    system = System(1, True)

    while future_events_list:
        event = future_events_list.pop()
        new_event = event.handle(system)
        if new_event:
            future_events_list.push(new_event)

    num_in_bank = 0
    print Customer.str_header()
    for customer in customers:
        print customer
        if customer.balked:
            num_in_bank += 1

    print "Number of Customers that went into the bank: %s" % num_in_bank

if __name__ == '__main__':
    main()