"""Build an original 16-macro rack using installed Live 11 device schemas."""
from pathlib import Path
import copy, gzip, math, struct, wave, os
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
CORE=Path(os.environ.get('INFISOUND_CORE_LIBRARY', '/Applications/Ableton Live 11 Intro.app/Contents/App-Resources/Core Library'))
DIST=Path(os.environ.get('INFISOUND_OUTPUT_DIR', str(ROOT/'dist'))).expanduser().resolve()
OUT=DIST/'Infisound'
(OUT/'Samples').mkdir(parents=True,exist_ok=True)
def read(p): return E.fromstring(gzip.decompress(p.read_bytes()))
def setv(e,p,v):
 x=e.find(p)
 assert x is not None,p
 x.set('Value',str(v).lower() if isinstance(v,bool) else str(v))
def manual(e,p,v):setv(e,p+'/Manual',v)
def clean(e):
 for parent in e.iter():
  for child in list(parent):
   if child.tag in ('KeyMidi','LockId','LockSeal'): parent.remove(child)
   elif child.tag in ('SourceContext','PresetRef'):child.clear()
   elif child.tag=='LastPresetRef':
    child.clear();E.SubElement(child,'Value')
 for x in e.iter('OverwriteProtectionNumber'):x.set('Value','0')
key=E.fromstring('<KeyMidi><PersistentKeyString Value=""/><IsNote Value="false"/><Channel Value="16"/><NoteOrController Value="0"/><LowerRangeNote Value="-1"/><UpperRangeNote Value="-1"/><ControllerMapMode Value="0"/></KeyMidi>')
def mapto(e,p,i,lo,hi):
 x=e.find(p);assert x is not None,p
 k=copy.deepcopy(key);setv(k,'NoteOrController',i);x.insert(1,k)
 rng=x.find('MidiControllerRange')
 if rng is None:
  rng=E.SubElement(x,'MidiControllerRange');E.SubElement(rng,'Min');E.SubElement(rng,'Max')
 setv(rng,'Min',lo);setv(rng,'Max',hi)
def fx(name):
 p=next((CORE/'Devices/Audio Effects'/name).rglob('*.adv'))
 d=copy.deepcopy(list(read(p))[0]);clean(d);setv(d,'UserName',name);return d
def wrap(d,i):
 d.set('Id','0')
 p=E.Element('AbletonDevicePreset',Id=str(i));E.SubElement(p,'OverwriteProtectionNumber',Value='0');E.SubElement(p,'Device').append(d);E.SubElement(p,'PresetRef');return p
root=read(CORE/'Racks/Instrument Racks/Evolving/Pitched Ambience.adg');clean(root)
g=root.find('GroupDevicePreset');rack=g.find('Device/InstrumentGroupDevice');branch=copy.deepcopy(g.find('BranchPresets/InstrumentBranchPreset'));simpler=copy.deepcopy(branch.find('.//OriginalSimpler'))
g.find('BranchPresets').clear();g.find('ReturnBranchPresets').clear()
setv(rack,'UserName','Infisound');setv(rack,'Annotation','Original waveform instrument. Play MIDI, then Rand. Wave selects 8 timbres. Volume is excluded from randomization.');setv(rack,'NumVisibleMacroControls',16)
setv(rack,'AreDevicesVisible',False);setv(rack,'IsBranchesListVisible',False)
names=['Lopass','F Env Amt','Wave','Attack','Sustain','Decay','Spread','Vol','Pitch Amt','Drive','Mod Amt','Mod Type','Delay Amt','Delay Time','Verb Amt','Verb Size']
values=[96,32,40,8,85,55,25,100,0,12,20,0,18,45,22,50]
colors=[47,47,56,55,55,55,42,69,55,4,41,41,45,45,39,39]
for i,(name,val,col) in enumerate(zip(names,values,colors)):
 setv(rack,f'MacroDisplayNames.{i}',name);manual(rack,f'MacroControls.{i}',val);setv(rack,f'MacroDefaults.{i}',val);setv(rack,f'MacroColor.{i}',col);setv(rack,f'ExcludeMacroFromRandomization.{i}',i==7);setv(rack,f'ForceDisplayGenericValue.{i}',i!=7)
mapto(rack,'ChainSelector',2,0,127);manual(rack,'ChainSelector',40)
f='Filter/Slot/Value/SimplerFilter/'
for p,v in {'Pitch/TransposeKey':0,'VolumeAndPan/Volume':-12,'VolumeAndPan/VolumeVelScale':.35,'VolumeAndPan/VolumeLfoAmount':0,'VolumeAndPan/PanoramaLfoAmount':0,'VolumeAndPan/PanoramaRnd':0,'Player/LoopModulators/LoopOn':True,'Lfo/IsOn':True,'Lfo/Slot/Value/SimplerLfo/Attack':.1,'Lfo/Slot/Value/SimplerLfo/Frequency':4.5,f+'Type':0,f+'Res':.18,f+'ModByPitch':.2,f+'ModByVelocity':0,f+'Envelope/Amount':18,f+'Freq':5000,f+'Envelope/DecayTime':650,'VolumeAndPan/Envelope/AttackTime':8,'VolumeAndPan/Envelope/DecayTime':800,'VolumeAndPan/Envelope/SustainLevel':.65,'VolumeAndPan/Envelope/ReleaseTime':250,'Globals/SpreadAmount':20}.items():manual(simpler,p,v)
for e in simpler.iter():
 if e.tag.startswith('ModConnections.'):
  setv(e,'Amount',0);setv(e,'Connection',0)
for p,i,lo,hi in [(f+'Freq',0,180,16000),(f+'Envelope/Amount',1,0,60),('VolumeAndPan/Envelope/AttackTime',3,2,2500),('VolumeAndPan/Envelope/SustainLevel',4,.05,1),('VolumeAndPan/Envelope/DecayTime',5,100,3500),('VolumeAndPan/Envelope/ReleaseTime',5,60,1800),(f+'Envelope/DecayTime',5,100,3500),('Globals/SpreadAmount',6,0,65),('Pitch/PitchLfoAmount',8,0,.025)]:mapto(simpler,p,i,lo,hi)
# Use native Chorus modes (Classic/Ensemble), controlled distortion, echo and room.
sat=fx('Saturator');manual(sat,'PreDrive',1);manual(sat,'PostDrive',-1);manual(sat,'DryWet',1);manual(sat,'PostClip',True);mapto(sat,'PreDrive',9,0,16);mapto(sat,'PostDrive',9,0,-12)
cho=fx('Chorus-Ensemble')
for p,v in {'Mode':0,'Rate':.8,'Amount':.4,'Feedback':.1,'OutputGain':1,'DryWet':.1}.items():manual(cho,p,v)
mapto(cho,'DryWet',10,0,.55);mapto(cho,'Mode',11,0,1)
del_=fx('Delay')
for p,v in {'DelayLine_Link':True,'DelayLine_SyncL':False,'DelayLine_SyncR':False,'DelayLine_TimeL':.28,'DelayLine_TimeR':.28,'Feedback':.28,'Modulation_AmountTime':0,'Modulation_AmountFilter':0,'DryWet':.08,'Filter_Frequency':2200,'Filter_Bandwidth':4}.items():manual(del_,p,v)
mapto(del_,'DryWet',12,0,.4)
for p in ['DelayLine_TimeL','DelayLine_TimeR']:mapto(del_,p,13,.08,.65)
rev=fx('Reverb')
for p,v in {'DecayTime':2200,'RoomSize':65,'MixDirect':.12,'MixReflect':.5,'MixDiffuse':.7,'StereoSeparation':100,'PreDelay':12}.items():manual(rev,p,v)
mapto(rev,'MixDirect',14,0,.45);mapto(rev,'RoomSize',15,15,100);mapto(rev,'DecayTime',15,450,6500)
lim=fx('Limiter');manual(lim,'Gain',0);manual(lim,'Ceiling',-3);manual(lim,'AutoRelease',True)
util=fx('Utility');manual(util,'ChannelMode',0);manual(util,'Gain',.501187);mapto(util,'Gain',7,.0630957,1)
wave_names=['Sine','Triangle','Saw','Square','Pulse','Hollow','Organ','Glass']
N=337;sr=44100
for index,name in enumerate(wave_names):
 samples=[]
 for n in range(N):
  t=2*math.pi*n/N
  if index==0:y=math.sin(t)
  elif index==1:y=sum((-1)**((h-1)//2)*math.sin(h*t)/h**2 for h in range(1,33,2))
  elif index==2:y=sum((-1)**(h+1)*math.sin(h*t)/h for h in range(1,33))
  elif index==3:y=sum(math.sin(h*t)/h for h in range(1,33,2))
  elif index==4:y=sum(math.sin(math.pi*h*.23)*math.cos(h*t)/h for h in range(1,33))
  elif index==5:y=math.sin(t)+.5*math.sin(3*t)+.25*math.sin(7*t)
  elif index==6:y=math.sin(t)+.65*math.sin(2*t)+.35*math.sin(4*t)+.18*math.sin(8*t)
  else:y=math.sin(t+1.8*math.sin(3*t))
  samples.append(y)
 peak=max(map(abs,samples));dest=OUT/'Samples'/f'{name}.wav'
 with wave.open(str(dest),'wb') as w:w.setparams((1,2,sr,N,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<h',round(y/peak*.7*32767)) for y in samples))
 b=copy.deepcopy(branch);b.set('Id',str(index));setv(b,'Name',name);b.find('DevicePresets').clear()
 for tag,v in [('Min',index*16),('Max',index*16+15),('CrossfadeMin',index*16),('CrossfadeMax',index*16+15)]:setv(b,'BranchSelectorRange/'+tag,v)
 mix=b.find('MixerPreset//AudioBranchMixerDevice');manual(mix,'Volume',1);manual(mix,'Panorama',0)
 s=copy.deepcopy(simpler);setv(s,'UserName',name)
 part=s.find('.//MultiSamplePart');setv(part,'Name',name+'.wav');setv(part,'RootKey',48);setv(part,'Detune',1200*math.log2((440*2**((48-69)/12))/(sr/N)));setv(part,'SampleStart',0);setv(part,'SampleEnd',N)
 for loop in ['SustainLoop','ReleaseLoop']:
  for p,v in [('Start',0),('End',N),('Mode',1 if loop=='SustainLoop' else 0),('Crossfade',0)]:setv(part,loop+'/'+p,v)
 ref=part.find('SampleRef');fr=ref.find('FileRef')
 for p,v in [('RelativePathType',0),('RelativePath',''),('Path',str(dest)),('LivePackName',''),('LivePackId',''),('OriginalFileSize',dest.stat().st_size),('OriginalCrc',0)]:setv(fr,p,v)
 setv(ref,'DefaultDuration',N);setv(ref,'DefaultSampleRate',sr)
 for tag in ['SlicePoints','ManualSlicePoints','BeatSlicePoints','RegionSlicePoints']:part.find(tag).clear()
 for i,d in enumerate([s,sat,cho,del_,rev,lim,util]):b.find('DevicePresets').append(wrap(copy.deepcopy(d),i))
 g.find('BranchPresets').append(b)
E.indent(root)
data=E.tostring(root,encoding='utf-8',xml_declaration=True)
(OUT/'Infisound.adg').write_bytes(gzip.compress(data))
print(OUT/'Infisound.adg')
print('8 original looped waves, 16 macros, 7 devices per chain')
