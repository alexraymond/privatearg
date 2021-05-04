def bound(value, low, high):
    return max(low, min(high, value))

def normalise(value, min_v, max_v):
    return (value - min_v) / (max_v - min_v)