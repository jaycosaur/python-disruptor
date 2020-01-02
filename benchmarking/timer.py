from time import perf_counter_ns

def timer(fn):
    def inner(*args):
        s_t = perf_counter_ns()
        res = fn(*args)
        print(f'{fn.__name__} time taken: {perf_counter_ns() - s_t}')
        return res
    
    return inner

def throttle_timer(fn):
    count = 0
    t_t = 0
    def inner(*args):
        nonlocal count, t_t
        s_t = perf_counter_ns()
        res = fn(*args)
        e_t = perf_counter_ns()
        count += 1
        t_t += (e_t-s_t)
        if count % 200000 == 0:
            print(f'{fn.__name__} time taken: {(t_t)/count}')
            count = 0
            t_t = 0

        return res
    
    return inner