"""Create the Remote Script edition, preserving Transform's audio graph."""
from pathlib import Path
import copy
import gzip
import os
import xml.etree.ElementTree as E

DIST = Path(os.environ.get('INFISOUND_OUTPUT_DIR', str(Path(__file__).resolve().parents[1] / 'dist'))).expanduser().resolve()
root = E.fromstring(gzip.decompress((DIST / 'Infisound Transform/Infisound Transform.adg').read_bytes()))
outer = root.find('GroupDevicePreset')
master = outer.find('Device/InstrumentGroupDevice')
devices = outer.find('BranchPresets/InstrumentBranchPreset/DevicePresets')
inner = devices[0]
drivers = inner.find('Device/InstrumentGroupDevice')
def setv(node, path, value):
    node.find(path).set('Value', str(value))
for child in list(devices)[1:]:
    devices.remove(child)
setv(master, 'UserName', 'Infisound Walk')
setv(drivers, 'UserName', 'Walking Sound')
setv(master, 'Annotation', 'Requires Infisound_Walk Control Surface. Independent random journeys. Rand retargets centers; Freeze pauses; Wander sets radius; Travel sets average seconds. Walking Sound shows actual values.')
# Mapping to an inert settings rack keeps the outer macros active in Live.
settings = copy.deepcopy(inner.find('BranchPresets/InstrumentBranchPreset/DevicePresets')[1])
settings.set('Id', '1')
settings_device = settings.find('Device/AudioEffectGroupDevice')
setv(settings_device, 'UserName', 'Walk Settings')
setv(settings_device, 'IsFolded', 'true')
for branch in settings.find('BranchPresets'):
    branch.find('DevicePresets').clear()
for i in range(16):
    param = settings_device.find(f'MacroControls.{i}')
    for key in list(param.findall('KeyMidi')): param.remove(key)
    key = E.fromstring('<KeyMidi><PersistentKeyString Value=""/><IsNote Value="false"/><Channel Value="16"/><NoteOrController Value="0"/><LowerRangeNote Value="-1"/><UpperRangeNote Value="-1"/><ControllerMapMode Value="0"/></KeyMidi>')
    setv(key, 'NoteOrController', i)
    param.insert(1,key)
    bounds = param.find('MidiControllerRange')
    if bounds is None:
        bounds = E.SubElement(param, 'MidiControllerRange')
        E.SubElement(bounds,'Min'); E.SubElement(bounds,'Max')
    setv(bounds,'Min',0); setv(bounds,'Max',127)
    setv(settings_device, f'MacroDisplayNames.{i}', master.find(f'MacroDisplayNames.{i}').get('Value'))
    # No control-surface target may also be owned by a macro mapping.
    if i != 14:
        for key in list(drivers.find(f'MacroControls.{i}').findall('KeyMidi')):
            drivers.find(f'MacroControls.{i}').remove(key)
    setv(master, f'MacroAnnotations.{i}', 'Random walk center; Rand chooses a new center.' if i in list(range(10))+[13] else '')
setv(master,'MacroDisplayNames.11','Wander')
setv(master,'MacroDisplayNames.15','Travel 2-60s')
setv(master,'MacroControls.15/Manual',60)
setv(master,'MacroDefaults.15',60)
setv(master,'MacroAnnotations.15','Average journey: 0=2s, 60=10s, 127=60s. Each dial varies its own duration from 65% to 145% of this.')
setv(master,'MacroAnnotations.11','Radius around each center: 0 returns to center, 127 explores the whole range.')
setv(master,'MacroAnnotations.12','0 linear travel; 127 eased departures and arrivals. No hold stage.')
devices.append(settings)
for lom in root.iter('LomId'): lom.set('Value','0')
assert not root.findall('.//MxDeviceAudioEffect')
assert len(root.findall('.//OriginalSimpler')) == 4
for i in list(range(10))+[13]:
    assert drivers.find(f'MacroControls.{i}/KeyMidi') is None
for i in (10,11,12,14,15):
    assert master.find(f'ExcludeMacroFromRandomization.{i}').get('Value') == 'true'
for path in root.findall('.//SampleRef/FileRef/Path'):
    assert Path(path.get('Value')).is_file()
E.indent(root)
output = DIST / 'Infisound Walk/Infisound Walk.adg'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(gzip.compress(E.tostring(root, encoding='utf-8', xml_declaration=True)))
print(output)
