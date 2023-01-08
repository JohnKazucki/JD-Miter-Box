

def clamp(number, minVal, maxVal):
    return max(minVal, min(number, maxVal))


def sign(n):
    if n<0: return -1
    elif n>0: return 1
    else: return None