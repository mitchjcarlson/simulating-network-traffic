import rng
from sim_model import *

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

    arrival_rng = rng.cumulative_emperical_rng(arrival_emp_prob)
    servers = [
        Server(rng.cumulative_emperical_rng(service_emp_prob))
    ]

    system = System(1, servers)
    customers = [Customer() for i in xrange(11)]

    future_events_list = events.EventList()
    future_events_list.push(FinishService(3, customers[0], servers[0]))
    servers[0].state = True

    arrival_time = 0
    for customer in customers[1:]:
        arrival_time += next(arrival_rng)
        future_events_list.push(Arrival(arrival_time, customer))


    while future_events_list:
        event = future_events_list.pop()
        new_event = event.handle(system)
        if new_event:
            future_events_list.push(new_event)

    num_in_bank = 0
    print "id\t%s" % Customer.str_header()
    for cid, customer in enumerate(customers):
        print "%s\t%s" % (cid, customer)
        if customer.balked:
            num_in_bank += 1

    print "Number of Customers that went into the bank: %s" % num_in_bank

if __name__ == '__main__':
    main()