import importlib.util
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('walk', Path(__file__).resolve().parents[1] / 'remote_scripts/Infisound_Walk/walk.py')
walk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walk)

class WalkTests(unittest.TestCase):
    def test_long_run_bounds_and_independent_destinations(self):
        lanes = [walk.Walk(64, random.Random(i)) for i in range(11)]
        destinations = [set() for _ in lanes]
        for _ in range(12000):
            for i, lane in enumerate(lanes):
                value = lane.step(.1, 64, 127, 60, 127)
                self.assertTrue(0 <= value <= 127)
                destinations[i].add(lane.target)
        self.assertTrue(all(len(d) > 75 for d in destinations))
        self.assertTrue(all(destinations[0].isdisjoint(d) for d in destinations[1:]))
        self.assertEqual(len(set(l.duration_factor for l in lanes)),11)

    def test_freeze_and_resume_preserve_state(self):
        lane = walk.Walk(64, random.Random(1))
        lane.step(1,64,127,60,127)
        before = vars(lane).copy()
        for _ in range(100): lane.step(.1,0,20,0,127,True,True)
        self.assertEqual(before,vars(lane))
        resumed = lane.step(.1,0,20,60,127,False,True)
        self.assertLess(abs(resumed-before['value']), .1)

    def test_zero_depth_returns_to_center_without_jump(self):
        lane = walk.Walk(100, random.Random(1))
        first = lane.step(.1,20,0,0,127,changed=True)
        self.assertGreater(first,99)
        for _ in range(40): lane.step(.1,20,0,0,127)
        self.assertAlmostEqual(lane.value,20)

    def test_speed_change_is_continuous(self):
        lane = walk.Walk(64,random.Random(1))
        lane.step(1,64,127,127,127)
        before = lane.value
        lane.step(0,64,127,0,127)
        self.assertEqual(before,lane.value)
        self.assertEqual(walk.seconds(0),2)
        self.assertEqual(walk.seconds(127),60)
        self.assertAlmostEqual(walk.seconds(60),10,delta=.03)

if __name__ == '__main__': unittest.main()
