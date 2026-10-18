"""Exercise the Live adapter with small API doubles; no Live install needed."""
import importlib
import sys
import types
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'remote_scripts'))

class Base:
    def __init__(self, song): self._song = song
    def song(self): return self._song
    def update_display(self): pass
    def disconnect(self): pass
    def log_message(self, message): pass

module = types.ModuleType('_Framework.ControlSurface')
module.ControlSurface = Base
sys.modules.setdefault('_Framework',types.ModuleType('_Framework'))
sys.modules['_Framework.ControlSurface'] = module
surface = importlib.import_module('Infisound_Walk.surface')

def parameter(name,value=64):
    return types.SimpleNamespace(name=name,value=value,is_enabled=True,automation_state=0)
class Device:
    def __init__(self,name,names):
        self.name=name
        self.class_name='InstrumentGroupDevice'
        self.parameters=[parameter('Device On',1)]+[parameter(n) for n in names]
        self.can_have_chains=True
        self.chains=[]

class SurfaceTests(unittest.TestCase):
    def setUp(self):
        self.outer=Device('Infisound Walk',surface.NAMES)
        self.inner=Device('Walking Sound',surface.NAMES)
        self.outer.chains=[types.SimpleNamespace(devices=[self.inner])]
        self.outer.parameters[11].value=0
        self.track=types.SimpleNamespace(devices=[self.outer])
        self.controller=surface.InfisoundWalk(types.SimpleNamespace(tracks=[self.track],return_tracks=[]))
        self.controller._discover()

    def test_character_adapter_moves_envelopes_and_protects_output(self):
        self.outer.name='Infisound Character'
        self.inner.name='Character Sound'
        self.outer.parameters[10].name='Character'
        self.outer.parameters[10].value=0
        self.controller._walk_racks={}
        self.controller._discover()
        self.assertEqual(len(self.controller._walk_racks[self.outer][2]),15)
        self.controller._last_tick-=.1
        self.controller.update_display()
        self.assertEqual(self.inner.parameters[15].value,64)
        for i in (9,10,11,12,15):
            self.assertNotEqual(self.inner.parameters[i+1].value,64)

    def test_discovers_and_removes_instances(self):
        self.assertEqual(len(self.controller._walk_racks),1)
        self.track.devices=[]
        self.controller._discover()
        self.assertFalse(self.controller._walk_racks)

    def test_writes_only_unautomated_lanes(self):
        self.inner.parameters[1].automation_state=1
        self.controller._last_tick-=.1
        self.controller.update_display()
        self.assertEqual(self.inner.parameters[1].value,64)
        self.assertNotEqual(self.inner.parameters[2].value,64)
        for i in (10,11,12,14,15):
            self.assertEqual(self.inner.parameters[i+1].value,64)

    def test_freeze_and_disabled_rack(self):
        for index in (11,0):
            self.outer.parameters[index].value=127 if index==11 else 0
            self.controller._last_tick-=.1
            self.controller.update_display()
            self.assertTrue(all(p.value==64 for p in self.inner.parameters[1:]))
            self.outer.parameters[11].value=0

if __name__=='__main__': unittest.main()
