"""Live's main-thread display timer drives only explicitly marked Walk racks."""
import time
from _Framework.ControlSurface import ControlSurface
from .walk import Walk, LANES
from .characters import Character, CHARACTER_LANES

NAMES = ('Tone', 'Texture', 'Space', 'Envelope', 'Width', 'Resonance',
         'Echo', 'Grain', 'Material', 'Pan Speed', 'Freeze', 'Wander',
         'Smooth', 'Morph', 'Output', 'Travel 2-60s')

CHARACTER_NAMES = NAMES[:9] + ('Character',) + NAMES[10:]

class InfisoundWalk(ControlSurface):
    def __init__(self, c_instance):
        super().__init__(c_instance)
        self._walk_racks = {}
        self._last_tick = time.monotonic()
        self._next_scan = 0.0
        self._reported_error = None
        self.log_message('Infisound Walk: controller ready')

    def _discover(self):
        found = {}
        def visit(devices):
            for device in devices:
                if device.class_name == 'InstrumentGroupDevice' and device.name in ('Infisound Walk', 'Infisound Character'):
                    children = [d for c in device.chains for d in c.devices]
                    inner = next((d for d in children if d.name in ('Walking Sound', 'Character Sound')), None)
                    if inner is not None:
                        outer_params = list(device.parameters)[1:17]
                        inner_params = list(inner.parameters)[1:17]
                        if len(outer_params) == 16 and len(inner_params) == 16 and tuple(p.name for p in outer_params) == (CHARACTER_NAMES if device.name == 'Infisound Character' else NAMES):
                            old = self._walk_racks.get(device)
                            found[device] = old or (outer_params, inner_params,
                                {i: Walk(inner_params[i].value) for i in (CHARACTER_LANES if device.name == 'Infisound Character' else LANES)}, {'character': Character()} if device.name == 'Infisound Character' else {})
                if device.can_have_chains:
                    for chain in device.chains:
                        visit(chain.devices)
        for track in list(self.song().tracks) + list(self.song().return_tracks):
            visit(track.devices)
        if len(found) != len(self._walk_racks):
            self.log_message('Infisound Walk: controlling %d rack(s)' % len(found))
        self._walk_racks = found

    def update_display(self):
        super().update_display()
        now = time.monotonic()
        dt = min(.25, max(0.0, now-self._last_tick))
        self._last_tick = now
        try:
            if now >= self._next_scan:
                self._discover()
                self._next_scan = now + 1.0
            for device, (controls, targets, walks, previous) in list(self._walk_racks.items()):
                frozen = controls[10].value >= 64 or device.parameters[0].value == 0
                character = previous.get('character')
                if character:
                    character.update(controls[9].value, dt, controls[15].value, frozen)
                for i, walk in walks.items():
                    parameter = targets[i]
                    # Respect existing arrangement/clip automation and disabled parameters.
                    if not parameter.is_enabled or int(parameter.automation_state) != 0:
                        walk.value = parameter.value
                        walk.phase = 1.0
                        continue
                    center = controls[3].value if character and i in (9,10,11,12,15) else controls[i].value
                    settings = (center, controls[11].value, character.revision if character else 0)
                    bounds = character.bounds(i, center, settings[1]) if character else None
                    changed = previous.get(i) != settings
                    value = walk.step(dt, settings[0], settings[1], controls[15].value,
                                      controls[12].value, frozen, changed, bounds)
                    if not frozen:
                        previous[i] = settings
                        if abs(parameter.value-value) > .001:
                            parameter.value = value
            self._reported_error = None
        except Exception as error:
            message = repr(error)
            if message != self._reported_error:
                self.log_message('Infisound Walk: ' + message)
                self._reported_error = message
            self._walk_racks = {}
            self._next_scan = now + 1.0

    def disconnect(self):
        self._walk_racks.clear()
        super().disconnect()
