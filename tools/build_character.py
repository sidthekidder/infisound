"""Broaden Walk into character-directed envelopes and oscillator colors."""
from pathlib import Path
import gzip
import math
import os
import struct
import wave
import xml.etree.ElementTree as E

DIST = Path(os.environ.get('INFISOUND_OUTPUT_DIR', str(Path(__file__).resolve().parents[1] / 'dist'))).expanduser().resolve()
OUT = DIST / 'Infisound Character'
(OUT / 'Samples').mkdir(parents=True, exist_ok=True)
root = E.fromstring(gzip.decompress((DIST / 'Infisound Walk/Infisound Walk.adg').read_bytes()))
master = root.find('GroupDevicePreset/Device/InstrumentGroupDevice')
devices = root.find('GroupDevicePreset/BranchPresets/InstrumentBranchPreset/DevicePresets')
inner = devices[0].find('Device/InstrumentGroupDevice')
signal = devices[0].find('BranchPresets/InstrumentBranchPreset/DevicePresets')
sound = signal[0].find('Device/InstrumentGroupDevice')
fx = signal[1].find('Device/AudioEffectGroupDevice')

def setv(e,path,value): e.find(path).set('Value',str(value))
def mapto(e,path,index,low,high):
    p=e.find(path)
    assert p is not None,path
    for k in list(p.findall('KeyMidi')): p.remove(k)
    k=E.fromstring('<KeyMidi><PersistentKeyString Value=""/><IsNote Value="false"/><Channel Value="16"/><NoteOrController Value="0"/><LowerRangeNote Value="-1"/><UpperRangeNote Value="-1"/><ControllerMapMode Value="0"/></KeyMidi>')
    setv(k,'NoteOrController',index);p.insert(1,k)
    b=p.find('MidiControllerRange')
    if b is None:
        b=E.SubElement(p,'MidiControllerRange');E.SubElement(b,'Min');E.SubElement(b,'Max')
    setv(b,'Min',low);setv(b,'Max',high)

setv(master,'UserName','Infisound Character')
setv(inner,'UserName','Character Sound')
setv(master,'MacroDisplayNames.9','Character')
setv(master,'MacroControls.9/Manual',127)
setv(master,'MacroDefaults.9',127)
setv(master,'ExcludeMacroFromRandomization.9','true')
setv(master,'MacroAnnotations.9','0-25 Pads; 26-51 Leads; 52-76 Keys; 77-102 Plucks; 103-127 Mixed. Mixed changes family about every three Travel durations. Protected from Rand.')
setv(master,'Annotation','Requires updated Infisound_Walk control surface. Character chooses envelope/source ranges. Mixed wanders between families. Use long chords for pads and repeating notes to hear attack/decay changes.')
for i,name in {9:'Filter Env',10:'Attack',11:'Decay',12:'Sustain',15:'Release'}.items():
    setv(inner,f'MacroDisplayNames.{i}',name)
    setv(inner,f'MacroAnnotations.{i}','Independent envelope destination within the selected Character. Changes to attack/decay are most audible on new notes.')
for index,lane in [(1,9),(3,10),(4,12),(5,11),(6,15)]:
    mapto(sound,f'MacroControls.{index}',lane,0,127)
# Pan rate stays steady; the freed lane now owns the filter envelope.
for k in list(fx.find('MacroControls.9').findall('KeyMidi')): fx.find('MacroControls.9').remove(k)
setv(fx,'MacroControls.9/Manual',25)
for synth in root.findall('.//OriginalSimpler'):
    f='Filter/Slot/Value/SimplerFilter/'
    for path,i,low,high in [(f+'Freq',0,120,18000),(f+'Envelope/Amount',1,0,60),
        ('VolumeAndPan/Envelope/AttackTime',3,.5,6000),('VolumeAndPan/Envelope/DecayTime',5,40,5000),
        ('VolumeAndPan/Envelope/SustainLevel',4,.01,1),('VolumeAndPan/Envelope/ReleaseTime',6,30,8000),
        (f+'Envelope/AttackTime',3,.5,4000),(f+'Envelope/DecayTime',5,40,5000),
        (f+'Envelope/ReleaseTime',6,30,6000)]:
        mapto(synth,path,i,low,high)
    setv(synth,f+'Envelope/SustainLevel/Manual',.15)
    mapto(synth,'Globals/SpreadAmount',7,0,95)

# Four distinct periodic sources. Stereo spread and chorus provide detuning;
# FM color is precomputed, not a real-time FM operator network.
functions = [
 ('Round',lambda t: math.sin(t)+.17*math.sin(2*t)+.08*math.sin(3*t)),
 ('Saw',lambda t: sum(math.sin(h*t)/h for h in range(1,33))),
 ('FM Bell',lambda t: math.sin(t+1.4*math.sin(3*t))),
 ('Pulse',lambda t: sum(math.sin(math.pi*h*.22)*math.cos(h*t)/h for h in range(1,33))),
]
for synth,(name,fn) in zip(root.findall('.//OriginalSimpler'),functions):
    n=337; samples=[fn(2*math.pi*j/n) for j in range(n)]
    mean=sum(samples)/n;samples=[v-mean for v in samples]
    sine=[math.sin(2*math.pi*j/n) for j in range(n)]
    fundamental=2*sum(v*s for v,s in zip(samples,sine))/n
    if fundamental<0: samples=[-v for v in samples];fundamental=-fundamental
    samples=[v+max(0,.35-fundamental)*s for v,s in zip(samples,sine)]
    rms=math.sqrt(sum(v*v for v in samples)/n)
    gain=min(.35/rms,.85/max(map(abs,samples)))
    path=OUT/'Samples'/f'{name}.wav'
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,44100,n,'NONE','not compressed'))
        w.writeframes(b''.join(struct.pack('<h',round(v*gain*32767)) for v in samples))
    setv(synth,'UserName',name)
    part=synth.find('.//MultiSamplePart')
    setv(part,'Name',name+'.wav')
    setv(part,'SampleRef/FileRef/Path',path)
    setv(part,'SampleRef/FileRef/OriginalFileSize',path.stat().st_size)
# Update chain/pair labels to match the new sources.
for b in signal[0].findall('.//InstrumentBranchPreset'):
    name=b.find('Name')
    if name is not None:
        name.set('Value',name.get('Value').replace('Sine','Round').replace('Metal','FM Bell').replace('Vowel','Pulse'))
for d in signal[0].findall('.//InstrumentGroupDevice'):
    name=d.find('UserName')
    name.set('Value',name.get('Value').replace('Sine','Round').replace('Metal','FM Bell').replace('Vowel','Pulse'))
assert len(root.findall('.//OriginalSimpler'))==4
assert not root.findall('.//MxDeviceAudioEffect')
for i in list(range(14))+[15]: assert inner.find(f'MacroControls.{i}/KeyMidi') is None
for p in root.findall('.//SampleRef/FileRef/Path'): assert Path(p.get('Value')).is_file()
E.indent(root)
output=OUT/'Infisound Character.adg'
output.write_bytes(gzip.compress(E.tostring(root,encoding='utf-8',xml_declaration=True)))
print(output)
