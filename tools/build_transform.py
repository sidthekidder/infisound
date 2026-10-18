"""Build a four-source continuously transforming rack from Evolving."""
from pathlib import Path
import copy
import gzip
import os
import json
import math
import struct
import wave
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
DIST = Path(os.environ.get('INFISOUND_OUTPUT_DIR', str(ROOT / 'dist'))).expanduser().resolve()
SAMPLES = DIST / 'Infisound Transform/Samples'
SAMPLES.mkdir(parents=True, exist_ok=True)

def rate_value(seconds):
    # Live 11 LFO frequency dial uses an 8/3 power curve, not raw Hz.
    # 10 s was independently calibrated through Live at 4.22948265.
    return 40 * ((1 / seconds) / 40) ** (3 / 8)

RATE_FAST, RATE_SLOW = rate_value(2), rate_value(60)
RATE_DEFAULT = round(127 * (rate_value(10) - RATE_FAST) / (RATE_SLOW - RATE_FAST))
source_audio = []

def prepare_sample(name, synth):
    source = Path(synth.find('.//SampleRef/FileRef/Path').get('Value'))
    with wave.open(str(source), 'rb') as wav:
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
        rate = wav.getframerate()
        samples = [v / 32768 for v in struct.unpack('<' + 'h' * wav.getnframes(), wav.readframes(wav.getnframes()))]
    sine = [math.sin(2 * math.pi * i / len(samples)) for i in range(len(samples))]
    fundamental = 2 * sum(a*b for a,b in zip(samples, sine)) / len(samples)
    if fundamental < 0:
        samples = [-v for v in samples]
        fundamental = -fundamental
    # Preserve each source's harmonics while giving every blend a shared,
    # in-phase fundamental. Never overwrite Expanded's original samples.
    samples = [v + max(0, .30 - fundamental) * s for v,s in zip(samples, sine)]
    rms = math.sqrt(sum(v*v for v in samples) / len(samples))
    gain = min(.35 / rms, .85 / max(map(abs, samples)))
    samples = [v * gain for v in samples]
    output = SAMPLES / f'{name}.wav'
    with wave.open(str(output), 'wb') as wav:
        wav.setparams((1, 2, rate, len(samples), 'NONE', 'not compressed'))
        wav.writeframes(b''.join(struct.pack('<h', round(v*32767)) for v in samples))
    ref = synth.find('.//SampleRef/FileRef')
    setv(ref, 'Path', output)
    setv(ref, 'OriginalFileSize', output.stat().st_size)
    source_audio.append(samples)

def setv(e, path, value):
    node = e.find(path)
    assert node is not None, path
    node.set('Value', str(value).lower() if isinstance(value, bool) else str(value))

def mapto(e, path, macro, low, high):
    node = e.find(path)
    assert node is not None, path
    for child in list(node):
        if child.tag == 'KeyMidi':
            node.remove(child)
    key = E.fromstring('<KeyMidi><PersistentKeyString Value=""/><IsNote Value="false"/><Channel Value="16"/><NoteOrController Value="0"/><LowerRangeNote Value="-1"/><UpperRangeNote Value="-1"/><ControllerMapMode Value="0"/></KeyMidi>')
    setv(key, 'NoteOrController', macro)
    node.insert(1, key)
    bounds = node.find('MidiControllerRange')
    if bounds is None:
        bounds = E.SubElement(node, 'MidiControllerRange')
        E.SubElement(bounds, 'Min')
        E.SubElement(bounds, 'Max')
    setv(bounds, 'Min', low)
    setv(bounds, 'Max', high)

def fade(branch, rising):
    # Full MIDI zones keep both voices triggered even at a silent fade endpoint.
    for tag, value in {'Min': 0, 'Max': 127,
                       'CrossfadeMin': 127 if rising else 0,
                       'CrossfadeMax': 127 if rising else 0}.items():
        setv(branch, 'BranchSelectorRange/' + tag, value)

root = E.fromstring(gzip.decompress((DIST / 'Infisound Evolving/Infisound Evolving.adg').read_bytes()))
outer = root.find('GroupDevicePreset')
master = outer.find('Device/InstrumentGroupDevice')
devices = outer.find('BranchPresets/InstrumentBranchPreset/DevicePresets')
inner = devices[0]
drivers = inner.find('Device/InstrumentGroupDevice')
signal = inner.find('BranchPresets/InstrumentBranchPreset/DevicePresets')
sound = signal[0]
sound_controls = sound.find('Device/InstrumentGroupDevice')
fx_controls = signal[1].find('Device/AudioEffectGroupDevice')

setv(master, 'UserName', 'Infisound Transform')
setv(drivers, 'UserName', 'Moving Sound')
setv(master, 'Annotation', 'Rand changes movement centers. Moving Sound shows actual values. Morph and Material crossfade four sustained sources. Output stays manual.')
for rack in (master, drivers):
    for index, name in {3: 'Envelope', 8: 'Material', 13: 'Morph', 15: 'Env Depth'}.items():
        setv(rack, f'MacroDisplayNames.{index}', name)
    setv(rack, 'MacroControls.11/Manual', 127)
    setv(rack, 'MacroDefaults.11', 127)
    setv(rack, 'MacroControls.13/Manual', 64)
    setv(rack, 'MacroDefaults.13', 64)
setv(master, 'ExcludeMacroFromRandomization.13', False)
setv(master, 'MacroDisplayNames.15', 'Sweep 2-60s')
setv(master, 'MacroControls.15/Manual', RATE_DEFAULT)
setv(master, 'MacroDefaults.15', RATE_DEFAULT)
setv(master, 'MacroAnnotations.15', 'Cycle time: 0 = 2s, 80 = about 10s, 127 = 60s. Higher values are slower. Excluded from Rand.')
# Env Depth stays fixed internally; the outer slot now controls all LFO rates.
for child in list(drivers.find('MacroControls.15')):
    if child.tag == 'KeyMidi': drivers.find('MacroControls.15').remove(child)
# Morph is driven by an LFO; do not also map it from its outer center control.
for key in list(drivers.find('MacroControls.13')):
    if key.tag == 'KeyMidi':
        drivers.find('MacroControls.13').remove(key)

# Broader continuous tone/envelope movement. Leave filter/effect enums fixed.
for index, lane, low, high in [(0,0,0,127), (1,15,0,110), (3,3,0,105),
                               (4,3,115,15), (5,3,5,125), (6,2,10,120),
                               (7,4,0,110), (8,5,0,110), (9,8,0,127)]:
    mapto(sound_controls, f'MacroControls.{index}', lane, low, high)
for index, lane, low, high in [(0,1,0,127), (2,1,0,120), (4,5,0,110),
                               (6,7,0,127), (7,7,127,0), (10,6,0,110),
                               (13,2,0,127), (14,2,0,127)]:
    mapto(fx_controls, f'MacroControls.{index}', lane, low, high)

branches = sound.find('BranchPresets')
original = {b.find('Name').get('Value'): copy.deepcopy(b) for b in branches}
pair_template = copy.deepcopy(sound)
branches.clear()
for pair_index, names in enumerate([('Sine', 'Saw'), ('Metal', 'Vowel')]):
    pair = copy.deepcopy(pair_template)
    pair.set('Id', '0')
    controls = pair.find('Device/InstrumentGroupDevice')
    setv(controls, 'UserName', ' / '.join(names))
    for index in range(16):
        mapto(controls, f'MacroControls.{index}', index, 0, 127)
    mapto(controls, 'ChainSelector', 9, 0, 127)
    setv(controls, 'ChainSelector/Manual', 64)
    children = pair.find('BranchPresets')
    children.clear()
    for index, name in enumerate(names):
        voice = copy.deepcopy(original[name])
        voice.set('Id', str(index))
        fade(voice, index == 1)
        synth = voice.find('.//OriginalSimpler')
        filter_type = synth.find('Filter/Slot/Value/SimplerFilter/Type')
        for key in list(filter_type):
            if key.tag == 'KeyMidi': filter_type.remove(key)
        setv(filter_type, 'Manual', 0)
        prepare_sample(name, synth)
        children.append(voice)
    branch = copy.deepcopy(original['Sine'])
    branch.set('Id', str(pair_index))
    setv(branch, 'Name', ' / '.join(names))
    branch.find('DevicePresets').clear()
    branch.find('DevicePresets').append(pair)
    fade(branch, pair_index == 1)
    # Extra headroom for simultaneous voices and overlapping fades.
    setv(branch, 'MixerPreset/AbletonDevicePreset/Device/AudioBranchMixerDevice/Volume/Manual', .5)
    branches.append(branch)

# Broaden source tone and wet effects without changing final gain or limiter.
for synth in sound.findall('.//OriginalSimpler'):
    mapto(synth, 'Filter/Slot/Value/SimplerFilter/Freq', 0, 500, 18000)
    setv(synth, 'Filter/Slot/Value/SimplerFilter/ModByPitch/Manual', 1)
    mapto(synth, 'Filter/Slot/Value/SimplerFilter/ModByLfo', 10, 0, .15)
    mapto(synth, 'Filter/Slot/Value/SimplerFilter/Res', 8, .05, .55)
    mapto(synth, 'VolumeAndPan/Envelope/AttackTime', 3, 2, 180)
    mapto(synth, 'VolumeAndPan/Envelope/SustainLevel', 4, .35, 1)
    mapto(synth, 'VolumeAndPan/Envelope/DecayTime', 5, 200, 3500)
for redux in root.findall('.//Redux2'):
    mapto(redux, 'DryWet', 6, 0, .7)

# Add a dedicated Morph LFO. Existing Material lane now controls the other axis.
new_lfo = copy.deepcopy(devices[1])
new_lfo.set('Id', str(len(devices)))
lfo = new_lfo.find('Device/MxDeviceAudioEffect')
setv(lfo, 'UserName', 'Evolve Morph')
setv(drivers, 'MacroControls.13/LomId', 1013)
for ref in lfo.findall('IdRefList/IdRefList/*'):
    setv(ref, 'LomId', 1013)
parameters = {p.find('Name').get('Value'): p for p in lfo.findall('ParameterList/ParameterList/*')}
setv(parameters['Phase'], 'Timeable/Manual', 37)
mapto(parameters['Offset'], 'Timeable', 13, -20, 20)
devices.append(new_lfo)
for index, preset in enumerate(list(devices)[1:]):
    lfo = preset.find('Device/MxDeviceAudioEffect')
    params = {p.find('Name').get('Value'): p for p in lfo.findall('ParameterList/ParameterList/*')}
    mapto(params['Freq Rate'], 'Timeable', 15, RATE_FAST, RATE_SLOW)
    setv(params['Freq Rate'], 'Timeable/Manual', rate_value(10))
    if index == 8: setv(lfo, 'UserName', 'Evolve Material')
    # Use the full modulation range instead of the old 20–80% window.
    blob = lfo.find('.//Blob')
    state = json.loads(bytes.fromhex(blob.text).rstrip(b'\x00').decode())
    state['TargetMin[7]'] = [0]
    state['TargetMax[7]'] = [100]
    blob.text = (json.dumps(state) + '\n\x00').encode().hex().upper()

assert len(root.findall('.//OriginalSimpler')) == 4
assert len(root.findall('.//MxDeviceAudioEffect')) == 11
for group in [sound] + list(sound.findall('BranchPresets/InstrumentBranchPreset/DevicePresets/GroupDevicePreset')):
    zones = group.find('BranchPresets')
    assert len(zones) == 2
    for branch in zones:
        assert branch.find('BranchSelectorRange/Min').get('Value') == '0'
        assert branch.find('BranchSelectorRange/Max').get('Value') == '127'
    assert zones[0].find('BranchSelectorRange/CrossfadeMax').get('Value') == '0'
    assert zones[1].find('BranchSelectorRange/CrossfadeMin').get('Value') == '127'
assert master.find('ExcludeMacroFromRandomization.14').get('Value') == 'true'
assert master.find('ExcludeMacroFromRandomization.13').get('Value') == 'false'
for synth in root.findall('.//OriginalSimpler'):
    assert synth.find('Filter/Slot/Value/SimplerFilter/Type/KeyMidi') is None
for i in list(range(10)) + [13]:
    assert sum(e.get('Value') == str(1000+i) for e in root.iter('LomId')) == 4
assert drivers.find('MacroControls.13/KeyMidi') is None
assert drivers.find('MacroControls.15/KeyMidi') is None
assert master.find('ExcludeMacroFromRandomization.15').get('Value') == 'true'
assert abs(rate_value(10) - 4.22948265) < .00001
assert RATE_DEFAULT == 80
for lfo in root.findall('.//MxDeviceAudioEffect'):
    rate = next(p for p in lfo.findall('ParameterList/ParameterList/*') if p.find('Name').get('Value') == 'Freq Rate')
    assert rate.find('Timeable/KeyMidi/NoteOrController').get('Value') == '15'
# Sweep a grid of linear blend weights, including every corner and midpoint.
# This checks source cancellation, not Live's downstream filters or perceived loudness.
minimum_rms = 1
for x in range(17):
    for y in range(17):
        a, b = x/16, y/16
        weights = [(1-a)*(1-b), (1-a)*b, a*(1-b), a*b]
        blend = [sum(w*s[i] for w,s in zip(weights, source_audio)) for i in range(len(source_audio[0]))]
        minimum_rms = min(minimum_rms, math.sqrt(sum(v*v for v in blend)/len(blend)))
assert minimum_rms > .20, minimum_rms
for path in root.findall('.//SampleRef/FileRef/Path'):
    assert Path(path.get('Value')).is_file()
E.indent(root)
output = DIST / 'Infisound Transform/Infisound Transform.adg'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(gzip.compress(E.tostring(root, encoding='utf-8', xml_declaration=True)))
print(output)
print('PASS: four always-addressable voices, three complementary crossfade pairs, eleven LFOs, protected output, sample paths resolved.')
print(f'PASS: 289 source blends, minimum RMS {minimum_rms:.3f}; all 11 LFO rates mapped to protected 2–60s control.')
