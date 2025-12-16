import time
from functools import wraps

def measure_latency(func):
    """
    A decorator to calculate the latency of a method or function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        latency = (time.perf_counter() - start) * 1000
        print(f"{wrapper.__name__} latency: {latency:.3f} ms")
        return result
    return wrapper