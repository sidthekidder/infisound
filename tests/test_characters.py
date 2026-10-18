import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'remote_scripts'))
from Infisound_Walk.characters import Character, PROFILES, CHARACTER_LANES
from Infisound_Walk.walk import Walk

class CharacterTests(unittest.TestCase):
    def test_selectors_and_freeze(self):
        c=Character(random.Random(4))
        for value,family in [(0,'Pads'),(25,'Pads'),(26,'Leads'),(51,'Leads'),(52,'Keys'),(76,'Keys'),(77,'Plucks'),(102,'Plucks')]:
            c.update(value,.1,60,False)
            self.assertEqual(c.family,family)
        before=(c.family,c.elapsed,c.revision)
        c.update(0,100,0,True)
        self.assertEqual(before,(c.family,c.elapsed,c.revision))

    def test_mixed_changes_family_without_a_shared_lane_phase(self):
        c=Character(random.Random(2));c.update(127,0,0,False)
        old=c.family;c.update(127,6.1,0,False)
        self.assertNotEqual(old,c.family)

    def test_bounds_and_destinations_for_every_family(self):
        for family,ranges in PROFILES.items():
            c=Character();c.family=family
            self.assertEqual(len(ranges),len(CHARACTER_LANES))
            for lane,(low,high) in zip(CHARACTER_LANES,ranges):
                self.assertTrue(0<=low<=high<=127)
                for center in (0,64,127):
                    bounds=c.bounds(lane,center,127)
                    self.assertEqual(bounds,(low,high))
                    w=Walk(64,random.Random(lane))
                    w.step(.1,center,127,60,127,bounds=bounds)
                    self.assertTrue(low<=w.target<=high)
                    narrow=c.bounds(lane,center,0)
                    self.assertEqual(narrow[0],narrow[1])

    def test_family_change_does_not_jump(self):
        c=Character();c.family='Pads'
        w=Walk(64,random.Random(7))
        w.step(1,64,127,60,127,bounds=c.bounds(10,64,127))
        value=w.value;c.family='Plucks'
        w.step(0,64,127,60,127,changed=True,bounds=c.bounds(10,64,127))
        self.assertEqual(w.value,value)
        self.assertLessEqual(w.target,.5)

if __name__=='__main__':unittest.main()
