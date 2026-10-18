"""Build Infisound Expanded: independent Sound and FX randomization banks."""
from pathlib import Path
import copy,gzip,math,struct,wave,os
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
CORE=Path(os.environ.get('INFISOUND_CORE_LIBRARY', '/Applications/Ableton Live 11 Intro.app/Contents/App-Resources/Core Library'))
DIST=Path(os.environ.get('INFISOUND_OUTPUT_DIR', str(ROOT/'dist'))).expanduser().resolve()
OUT=DIST/'Infisound Expanded';(OUT/'Samples').mkdir(parents=True,exist_ok=True)
def read(p):return E.fromstring(gzip.decompress(p.read_bytes()))
def setv(e,p,v):
 x=e.find(p);assert x is not None,p
 x.set('Value',str(v).lower() if isinstance(v,bool) else str(v))
def manual(e,p,v):setv(e,p+'/Manual',v)
def unmap(e):
 for parent in e.iter():
  for c in list(parent):
   if c.tag=='KeyMidi':parent.remove(c)
def mapto(e,p,i,lo,hi):
 x=e.find(p);assert x is not None,p
 k=E.fromstring('<KeyMidi><PersistentKeyString Value=""/><IsNote Value="false"/><Channel Value="16"/><NoteOrController Value="0"/><LowerRangeNote Value="-1"/><UpperRangeNote Value="-1"/><ControllerMapMode Value="0"/></KeyMidi>');setv(k,'NoteOrController',i);x.insert(1,k)
 rng=x.find('MidiControllerRange')
 if rng is None:
  rng=E.SubElement(x,'MidiControllerRange');E.SubElement(rng,'Min');E.SubElement(rng,'Max')
 setv(rng,'Min',lo);setv(rng,'Max',hi)
def wrap(d,i):
 d.set('Id','0');p=E.Element('AbletonDevicePreset',Id=str(i));E.SubElement(p,'OverwriteProtectionNumber',Value='0');E.SubElement(p,'Device').append(d);E.SubElement(p,'PresetRef');return p
def setup(r,name,names,values):
 unmap(r);setv(r,'UserName',name);setv(r,'NumVisibleMacroControls',len(names));setv(r,'AreDevicesVisible',False);setv(r,'IsBranchesListVisible',False)
 r.find('MacroVariations/MacroSnapshots').clear();setv(r,'AreMacroVariationsControlsVisible',False)
 colors=[20,20,26,24,24,24,24,21,20,20,21,21,21,21,22,22]
 for i in range(16):
  setv(r,f'MacroDisplayNames.{i}',names[i] if i<len(names) else f'Macro {i+1}');manual(r,f'MacroControls.{i}',values[i] if i<len(values) else 0);setv(r,f'MacroDefaults.{i}',values[i] if i<len(values) else 0);setv(r,f'ExcludeMacroFromRandomization.{i}',False);setv(r,f'ForceDisplayGenericValue.{i}',True);setv(r,f'MacroColor.{i}',colors[i])
def fx(category):
 r=read(next((CORE/'Devices/Audio Effects'/category).rglob('*.adv')));d=list(r)[0];unmap(d);setv(d,'UserName',category);return d
v1=read(DIST/'Infisound/Infisound.adg');sound=copy.deepcopy(v1.find('GroupDevicePreset'));sound.set('Id','0')
sr=sound.find('Device/InstrumentGroupDevice')
setup(sr,'01 SOUND - Rand',['Cutoff','Filter Env','Wave','Attack','Sustain','Decay','Release','Spread','Resonance','Filter Type','Filter Move','Move Rate','Move Shape','Vibrato','Velocity','Glide'],[96,32,20,8,85,55,40,25,20,0,0,45,0,0,50,0])
setv(sr,'Annotation','Randomize the instrument independently of FX. Filter Type: LP, HP, BP, notch. Move Shape: six LFO waveforms. Glide is active in glide mode.');mapto(sr,'ChainSelector',2,0,127);manual(sr,'ChainSelector',20)
branches=sound.find('BranchPresets');template=copy.deepcopy(branches[0]);s0=copy.deepcopy(template.find('.//OriginalSimpler'));unmap(s0);branches.clear()
f='Filter/Slot/Value/SimplerFilter/';l='Lfo/Slot/Value/SimplerLfo/'
for p,v in {f+'ModByLfo':0,f+'Res':.18,f+'Type':0,l+'Type':0,l+'Frequency':2,l+'Attack':.1,'Pitch/PitchLfoAmount':0,'Globals/PortamentoMode':1,'Globals/PortamentoTime':.1}.items():manual(s0,p,v)
SOUND_MAP=[(f+'Freq',0,180,16000),(f+'Envelope/Amount',1,0,60),('VolumeAndPan/Envelope/AttackTime',3,2,2500),('VolumeAndPan/Envelope/SustainLevel',4,.05,1),('VolumeAndPan/Envelope/DecayTime',5,100,3500),(f+'Envelope/DecayTime',5,100,3500),('VolumeAndPan/Envelope/ReleaseTime',6,30,2500),('Globals/SpreadAmount',7,0,65),(f+'Res',8,.05,.65),(f+'Type',9,0,3),(f+'ModByLfo',10,0,.45),(l+'Frequency',11,.12,9),(l+'Type',12,0,5),('Pitch/PitchLfoAmount',13,0,.02),('VolumeAndPan/VolumeVelScale',14,.1,.8),('Globals/PortamentoTime',15,.1,180)]
for p,i,lo,hi in SOUND_MAP:mapto(s0,p,i,lo,hi)
wave_names=['Sine','Triangle','Saw','Square','Pulse','Hollow','Organ','Glass','Reed','Bell','Soft Buzz','Narrow Pulse','Octave Stack','Fifths','Metal','Vowel']
N=337;rate=44100
for i,name in enumerate(wave_names):
 samples=[]
 for n in range(N):
  t=2*math.pi*n/N
  if i==0:y=math.sin(t)
  elif i==1:y=sum((-1)**((h-1)//2)*math.sin(h*t)/h**2 for h in range(1,33,2))
  elif i==2:y=sum((-1)**(h+1)*math.sin(h*t)/h for h in range(1,33))
  elif i==3:y=sum(math.sin(h*t)/h for h in range(1,33,2))
  elif i in (4,11):y=sum(math.sin(math.pi*h*(.23 if i==4 else .08))*math.cos(h*t)/h for h in range(1,33))
  elif i==5:y=math.sin(t)+.5*math.sin(3*t)+.25*math.sin(7*t)
  elif i==6:y=math.sin(t)+.65*math.sin(2*t)+.35*math.sin(4*t)+.18*math.sin(8*t)
  elif i==7:y=math.sin(t+1.8*math.sin(3*t))
  elif i==8:y=sum(math.sin(h*t)/h**.65 for h in range(1,18,2))
  elif i==9:y=math.sin(t)+.45*math.sin(5*t)+.25*math.sin(9*t)+.12*math.sin(13*t)
  elif i==10:y=math.tanh(2.4*math.sin(t))+.15*math.sin(2*t)
  elif i==12:y=math.sin(t)+.7*math.sin(2*t)+.4*math.sin(4*t)
  elif i==13:y=math.sin(t)+.5*math.sin(3*t)+.22*math.sin(6*t)
  elif i==14:y=math.sin(t+2.8*math.sin(7*t))
  else:y=sum((.15/h+math.exp(-((h-5)/2)**2)+.4*math.exp(-((h-13)/3)**2))*math.sin(h*t) for h in range(1,33))
  samples.append(y)
 mean=sum(samples)/N;samples=[s-mean for s in samples];peak=max(map(abs,samples));path=OUT/'Samples'/f'{name}.wav'
 with wave.open(str(path),'wb') as w:w.setparams((1,2,rate,N,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<h',round(s/peak*.7*32767)) for s in samples))
 b=copy.deepcopy(template);b.set('Id',str(i));setv(b,'Name',name);b.find('DevicePresets').clear();s=copy.deepcopy(s0);setv(s,'UserName',name)
 for tag,val in [('Min',i*8),('Max',i*8+7),('CrossfadeMin',i*8),('CrossfadeMax',i*8+7)]:setv(b,'BranchSelectorRange/'+tag,val)
 part=s.find('.//MultiSamplePart');setv(part,'Name',name+'.wav');setv(part,'SampleRef/FileRef/Path',path);setv(part,'SampleRef/FileRef/OriginalFileSize',path.stat().st_size)
 b.find('DevicePresets').append(wrap(s,0));branches.append(b)
# One shared FX rack for every waveform; its Rand does not change the sound bank.
audio=read(CORE/'Racks/Audio Effect Racks/Mixing & Mastering/Drums Boombox.adg').find('GroupDevicePreset');audio.set('Id','1');ar=audio.find('Device/AudioEffectGroupDevice')
setup(ar,'02 FX - Rand',['Drive','Drive Type','Chorus','Chorus Rate','Phaser','Phase Type','Crush','Crush Rate','Pan Amt','Pan Rate','Delay','Delay Time','Feedback','Reverb','Space','Darkness'],[12,0,20,35,0,0,0,110,0,30,18,45,40,22,50,50])
setv(ar,'Annotation','Randomize effects independently. Feedback capped at 55%; crush and phaser mixes capped. Final limiter and volume are outside both banks.')
ab=copy.deepcopy(audio.find('BranchPresets')[0]);unmap(ab);ab.set('Id','0');setv(ab,'Name','Shared FX');setv(ab,'IsSoloed',False);ab.find('DevicePresets').clear()
for tag,val in [('Min',0),('Max',127),('CrossfadeMin',0),('CrossfadeMax',127)]:setv(ab,'BranchSelectorRange/'+tag,val)
manual(ab.find('.//AudioBranchMixerDevice'),'Volume',1)
audio.find('BranchPresets').clear();audio.find('BranchPresets').append(ab);audio.find('ReturnBranchPresets').clear()
base_devices=template.find('DevicePresets');devs={d.find('Device')[0].tag:copy.deepcopy(d.find('Device')[0]) for d in base_devices}
sat=devs['Saturator'];cho=devs['Chorus2'];delay=devs['Delay'];rev=devs['Reverb'];lim=devs['Limiter'];util=devs['StereoGain'];ph=fx('Phaser-Flanger');cr=fx('Redux');pan=fx('Auto Pan')
for d in [sat,cho,delay,rev,lim,util]:unmap(d)
for d,params in [(sat,{'Type':0}),(cho,{'Mode':1}),(ph,{'Mode':0,'Feedback':.2,'DryWet':0,'OutputGain':1,'Modulation_Sync':False,'Modulation_Sync2':False,'Modulation_Frequency':.3,'Modulation_Frequency2':.3}),(cr,{'DryWet':0,'SampleRate':22000,'BitDepth':12,'Jitter':0,'EnablePreFilter':True,'EnablePostFilter':True}),(pan,{'Lfo/Type':0,'Lfo/RateType':0,'Lfo/Frequency':.5,'Lfo/LfoAmount':0,'Lfo/LfoShape':0,'Lfo/LfoInvert':False,'Lfo/Phase':180})]:
 for p,v in params.items():manual(d,p,v)
FX_MAP=[(sat,'PreDrive',0,0,16),(sat,'PostDrive',0,0,-12),(sat,'Type',1,0,5),(cho,'DryWet',2,0,.55),(cho,'Rate',3,.15,3),(ph,'DryWet',4,0,.45),(ph,'Mode',5,0,2),(cr,'DryWet',6,0,.35),(cr,'SampleRate',7,4000,40000),(pan,'Lfo/LfoAmount',8,0,.65),(pan,'Lfo/Frequency',9,.08,5),(delay,'DryWet',10,0,.4),(delay,'DelayLine_TimeL',11,.08,.65),(delay,'DelayLine_TimeR',11,.08,.65),(delay,'Feedback',12,.1,.55),(rev,'MixDirect',13,0,.45),(rev,'RoomSize',14,15,100),(rev,'DecayTime',14,450,6500),(rev,'ShelfHiFreq',15,8000,1000)]
for d,p,i,lo,hi in FX_MAP:mapto(d,p,i,lo,hi)
for i,d in enumerate([sat,cho,ph,cr,pan,delay,rev]):ab.find('DevicePresets').append(wrap(d,i))
# Outer shell exposes only final volume; expand devices to see both banks.
outer=copy.deepcopy(v1);og=outer.find('GroupDevicePreset');orr=og.find('Device/InstrumentGroupDevice');setup(orr,'Infisound Expanded',['Output'],[96]);setv(orr,'ForceDisplayGenericValue.0',False);setv(orr,'ExcludeMacroFromRandomization.0',True);setv(orr,'AreDevicesVisible',True);setv(orr,'Annotation','Two independent randomization banks: SOUND and FX. Use each bank Rand button. Output stays fixed.');manual(orr,'ChainSelector',0)
ob=copy.deepcopy(template);ob.set('Id','0');setv(ob,'Name','Sound + Shared FX');ob.find('DevicePresets').clear()
for tag,val in [('Min',0),('Max',127),('CrossfadeMin',0),('CrossfadeMax',127)]:setv(ob,'BranchSelectorRange/'+tag,val)
ob.find('DevicePresets').append(sound);ob.find('DevicePresets').append(audio)
manual(util,'ChannelMode',1);manual(lim,'Ceiling',-3);manual(lim,'Gain',0);manual(util,'Gain',.501187);mapto(util,'Gain',0,.0630957,1)
ob.find('DevicePresets').append(wrap(lim,2));ob.find('DevicePresets').append(wrap(util,3));og.find('BranchPresets').clear();og.find('BranchPresets').append(ob)
# One top-level Rand: sixteen paired randomization dimensions across both banks.
setup(orr,'Infisound Expanded',['Tone','Contour','Character','Attack + Air','Body','Decay + Echo','Release + Space','Width + Pan','Reso + Phase','Filter + Room','Motion + Crush','Movement Rate','Motion Shape','Vibrato + Drive','Touch + Feedback','Glide + Echo'],[96,32,20,8,85,55,40,25,20,0,0,45,0,0,50,0])
setv(orr,'AreDevicesVisible',False)
setv(orr,'Annotation','Press this rack Rand to randomize SOUND and FX together. Sixteen master macros pair 32 bank controls. Final output stays fixed. Expand devices to inspect the banks; their controls are mapped to these masters.')
# Sound macro index -> FX macro index. Every FX control is driven exactly once.
fx_pairs=[15,5,1,3,2,10,14,8,4,13,6,9,7,0,12,11]
for i,j in enumerate(fx_pairs):
 mapto(sr,f'MacroControls.{i}',i,0,127)
 # Darker cutoff pairs with brighter reverb; faster modulation pairs with less crushing.
 mapto(ar,f'MacroControls.{j}',i,127 if j in (15,7) else 0,0 if j in (15,7) else 127)
unmap(util)
manual(util,'Gain',.501187)
# wrap() stores the same Utility element, so fixed gain applies to final output.

# Remove obsolete preset provenance and factory lock metadata from new construction.
for parent in outer.iter():
 for child in list(parent):
  if child.tag in ('LockId','LockSeal'):parent.remove(child)
  elif child.tag in ('SourceContext','PresetRef'):child.clear()
  elif child.tag=='LastPresetRef':child.clear();E.SubElement(child,'Value')
E.indent(outer);path=OUT/'Infisound Expanded.adg';path.write_bytes(gzip.compress(E.tostring(outer,encoding='utf-8',xml_declaration=True)))
print(path)
# Validate structural mappings, sample references and zone coverage.
assert len(sound.findall('.//OriginalSimpler'))==16
assert len(outer.findall('.//Reverb'))==1
for bank in [sound,audio]:
 ids={int(k.find('NoteOrController').get('Value')) for k in bank.iter('KeyMidi')};assert ids==set(range(16)),ids
zones=[]
for b in branches:
 z=b.find('BranchSelectorRange');zones+=range(int(z.find('Min').get('Value')),int(z.find('Max').get('Value'))+1)
assert sorted(zones)==list(range(128))
for p in outer.findall('.//SampleRef/FileRef/Path'):assert Path(p.get('Value')).is_file()
assert len(orr.findall('./MacroControls.0/KeyMidi'))==0
assert util.find('Gain/KeyMidi') is None
assert {int(k.find('NoteOrController').get('Value')) for k in sr.findall('./*/KeyMidi')}==set(range(16))
print('PASS: one global Rand, 16 paired master macros controlling 32 bank controls, fixed -6 dB output, 16 waveforms, shared FX, all samples resolve.')
