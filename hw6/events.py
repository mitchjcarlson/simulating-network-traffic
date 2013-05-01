import heapq
from rng import iter_random

class Event(object):

    def __init__(self, time, customer):
        self.time = time
        self.customer = customer

    def __lt__(self, other):
        return self.time < other.time

    def __le__(self, other):
        return self.time <= other.time

    def __eq__(self, other):
        return self.time == other.time

    def __ne__(self, other):
        return not self.time == other.time

    def __gt__(self, other):
        return self.time > other.time

    def __ge__(self, other):
        return self.time >= other.time

    def __str__(self):
        return "%s { time : %s , customer : %s }" % (type(self).__name__, self.time, self.customer)

class RandomEventMeta(type):

    rng = iter_random()

    def random(cls, current_time, *args, **kwargs):
        inter_arrive_time = next(cls.rng)
        event_time = inter_arrive_time + current_time
        return cls(event_time, *args, **kwargs)

class RandomEvent(Event):

    __metaclass__ = RandomEventMeta

class EventList(object):

    def __init__(self):
        self.events = []

    def push(self, event):
        heapq.heappush(self.events, event)

    def pop(self):
        return heapq.heappop(self.events)

    def __bool__(self):
        return bool(self.events)

    def __len__(self):
        return len(self.events)
