import random

def iter_random():
    """
    Wraps random number generator in an infinite iterable, allowing random
    floats to be retrieved with calls to next()
    """
    while 1:
        yield random.random()

def cumulative_emperical(emp):
    sum_prob = 0.0
    emp_cum_prob = []
    for val, prob in emp:
        sum_prob += prob;
        emp_cum_prob.append((val, sum_prob))
    return emp_cum_prob

def emperical_rng(emp):
    while 1:
        rand_float = random.random()
        for val, prob in emp:
            if rand_float < prob:
                yield val
                break