import rng
from sim_model import *

def main():
    arrival_emp_prob = [
         (1, 0.25),
         (2, 0.40),
         (3 ,0.20),
         (4, 0.15)
    ]

    able_emp_prob = [
         (2, 0.30),
         (3 ,0.28),
         (4, 0.25),
         (5, 0.17)
    ]

    baker_emp_prob = [
         (3, 0.35),
         (4 ,0.25),
         (5, 0.20),
         (6, 0.20)
    ]

    arrival_rng = rng.cumulative_emperical_rng(arrival_emp_prob)
    servers = [
        Server(rng.cumulative_emperical_rng(able_emp_prob)),
        Server(rng.cumulative_emperical_rng(baker_emp_prob))
    ]

    system = System(System.INFINITE_QUEUE, servers)
    customers = [Customer() for i in xrange(100)]

    future_events_list = events.EventList()

    arrival_time = 0
    for customer in customers[1:]:
        arrival_time += next(arrival_rng)
        future_events_list.push(Arrival(arrival_time, customer))


    while future_events_list:
        event = future_events_list.pop()
        new_event = event.handle(system)
        if new_event:
            future_events_list.push(new_event)

    print "id\t%s" % Customer.str_header()
    for cid, customer in enumerate(customers):
        print "%s\t%s" % (cid, customer)

if __name__ == '__main__':
    main()