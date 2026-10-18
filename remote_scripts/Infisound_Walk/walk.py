"""Independent bounded random destinations, interpolated without hold stages."""
import random

LANES = tuple(range(10)) + (13,)

def seconds(value):
    return 2.0 * 30.0 ** (value / 127.0)

class Walk:
    def __init__(self, value, rng=None):
        self.rng = rng or random.Random()
        self.value = self.start = self.target = value
        self.phase = 1.0
        self.duration_factor = 1.0

    def retarget(self, center, depth):
        self.start = self.value
        radius = 127.0 * depth / 127.0
        low, high = max(0.0, center-radius), min(127.0, center+radius)
        self.target = self.rng.uniform(low, high)
        self.duration_factor = self.rng.uniform(.65, 1.45)
        self.phase = 0.0

    def step(self, dt, center, depth, rate, smooth, frozen=False, changed=False):
        if frozen:
            return self.value
        if changed or self.phase >= 1.0:
            self.retarget(center, depth)
        self.phase = min(1.0, self.phase + dt / (seconds(rate)*self.duration_factor))
        t = self.phase
        eased = t*t*(3.0-2.0*t)
        t += (eased-t) * smooth/127.0
        self.value = self.start + (self.target-self.start)*t
        return self.value
