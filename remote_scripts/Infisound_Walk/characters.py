"""Musical destination ranges in macro units; all paths remain continuous."""
import random
from .walk import seconds

CHARACTER_LANES = tuple(range(14)) + (15,)
# Tone, drive/chorus, space, motion, width, resonance, echo, grain,
# source material, filter envelope, amp attack, decay, sustain, morph, release.
PROFILES = {
    'Pads': [(25,110),(10,65),(60,110),(10,65),(75,127),(5,60),(15,65),(0,20),
             (65,127),(5,40),(35,110),(50,120),(85,127),(0,45),(65,127)],
    'Leads': [(55,127),(25,95),(5,45),(0,35),(10,75),(15,85),(5,55),(0,35),
              (70,127),(15,85),(0,2),(10,55),(75,127),(20,95),(2,22)],
    'Keys': [(25,95),(0,45),(15,65),(0,20),(15,65),(0,40),(0,35),(0,12),
             (0,50),(25,85),(0,1),(12,65),(5,45),(55,127),(8,35)],
    'Plucks': [(30,120),(0,65),(10,60),(0,20),(20,90),(5,75),(15,80),(0,25),
               (20,110),(65,127),(0,0.5),(1,15),(0,8),(0,110),(1,12)],
}

class Character:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.mode = None
        self.family = 'Pads'
        self.elapsed = 0.0
        self.revision = 0

    def update(self, value, dt, rate, frozen):
        if frozen: return
        mode = min(4, int(value*5/128))
        changed = mode != self.mode
        self.elapsed += dt
        if changed or (mode == 4 and self.elapsed >= seconds(rate)*3):
            names = tuple(PROFILES)
            self.family = names[mode] if mode < 4 else self.rng.choice([n for n in names if n != self.family])
            self.elapsed = 0.0
            self.revision += 1
        self.mode = mode

    def bounds(self, lane, center, wander):
        low, high = PROFILES[self.family][CHARACTER_LANES.index(lane)]
        midpoint = low + (high-low)*center/127.0
        radius = (high-low)*wander/127.0
        return max(low, midpoint-radius), min(high, midpoint+radius)
