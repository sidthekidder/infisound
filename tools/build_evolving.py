"""Build a self-modulating Intro-compatible rack using the installed Ableton LFO."""
from pathlib import Path
import copy, gzip, json, os
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
CORE=Path(os.environ.get('INFISOUND_CORE_LIBRARY','/Applications/Ableton Live 11 Intro.app/Contents/App-Resources/Core Library'))
DIST=Path(os.environ.get('INFISOUND_OUTPUT_DIR',str(ROOT/'dist'))).expanduser().resolve()
OUT=DIST/'Infisound Evolving';OUT.mkdir(parents=True,exist_ok=True)
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
 for c in list(x):
  if c.tag=='KeyMidi':x.remove(c)
 k=E.fromstring('<KeyMidi><PersistentKeyString Value=""/><IsNote Value="false"/><Channel Value="16"/><NoteOrController Value="0"/><LowerRangeNote Value="-1"/><UpperRangeNote Value="-1"/><ControllerMapMode Value="0"/></KeyMidi>');setv(k,'NoteOrController',i);x.insert(1,k)
 rng=x.find('MidiControllerRange')
 if rng is None:
  rng=E.SubElement(x,'MidiControllerRange');E.SubElement(rng,'Min');E.SubElement(rng,'Max')
 setv(rng,'Min',lo);setv(rng,'Max',hi)
def wrap(d,i):
 d.set('Id','0');p=E.Element('AbletonDevicePreset',Id=str(i));E.SubElement(p,'OverwriteProtectionNumber',Value='0');E.SubElement(p,'Device').append(d);E.SubElement(p,'PresetRef');return p
root=read(DIST/'Infisound Expanded/Infisound Expanded.adg')
g=root.find('GroupDevicePreset');rack=g.find('Device/InstrumentGroupDevice');devices=g.find('BranchPresets/InstrumentBranchPreset/DevicePresets')
sound=devices[0].find('Device/InstrumentGroupDevice');fxrack=devices[1].find('Device/AudioEffectGroupDevice')
# Preserve each bank's own device mappings, remove only parent-to-bank links.
for bank in [sound,fxrack]:
 for i in range(16):unmap(bank.find(f'MacroControls.{i}'))
setv(rack,'UserName','Infisound Evolving');setv(rack,'Annotation','Continuous sine sweeps with randomized variation at 0.1 Hz. Hold a chord. Freeze holds the modulation outputs. Depth reduces movement around the center. Wave/type switches and pitch remain stable.');setv(rack,'AreDevicesVisible',False)
names=['Tone','Texture','Space','Motion','Width','Resonance','Echo','Grain','Brightness','Pan Speed','Freeze','Depth','Smooth','Wave','Output','Attack']
values=[64]*10+[0,100,127,20,96,35]
for i,(name,value) in enumerate(zip(names,values)):
 setv(rack,f'MacroDisplayNames.{i}',name);manual(rack,f'MacroControls.{i}',value);setv(rack,f'MacroDefaults.{i}',value);setv(rack,f'ExcludeMacroFromRandomization.{i}',True);setv(rack,f'ForceDisplayGenericValue.{i}',True)
 setv(rack,f'MacroAnnotations.{i}',('Automated by a smoothed sine LFO with jitter at 0.1 Hz.' if i<10 else {'Freeze':'0: moving; 127: hold current modulation values.','Depth':'Movement depth around each lane midpoint; changing it can shift the current value.','Smooth':'LFO smoothing, default 100%. Not an exact morph-duration control.','Wave':'Manual waveform selection; not swept automatically.','Output':'Final gain, excluded from automatic motion.','Attack':'Manual note attack time.'}[name]))
# Pair only continuous controls; never animate oscillator selection or effect enums.
sound_maps={0:(0,25,115),1:(0,5,65),3:(15,0,110),7:(4,0,80),8:(5,5,65),10:(3,0,70),11:(3,15,65)}
fx_maps={0:(1,0,70),2:(1,5,85),3:(3,5,75),4:(5,0,65),6:(7,0,45),7:(7,100,35),8:(4,0,85),9:(9,10,80),10:(6,5,85),12:(6,10,65),13:(2,10,90),14:(2,20,90),15:(8,15,100)}
for idx,(master,lo,hi) in sound_maps.items():mapto(sound,f'MacroControls.{idx}',master,lo,hi)
for idx,(master,lo,hi) in fx_maps.items():mapto(fxrack,f'MacroControls.{idx}',master,lo,hi)
mapto(sound,'MacroControls.2',13,0,127)
for idx,val in {4:127,5:70,6:75,9:0,12:0,13:0,14:45,15:0}.items():manual(sound,f'MacroControls.{idx}',val)
for idx,val in {1:0,5:0,11:45}.items():manual(fxrack,f'MacroControls.{idx}',val)
# Also serialize safe fixed values in the voices, rather than relying on macro refresh.
for s in root.findall('.//OriginalSimpler'):
 manual(s,'Pitch/PitchLfoAmount',0);manual(s,'Globals/PortamentoTime',.1)
 manual(s,'VolumeAndPan/Envelope/SustainLevel',1)
util=devices[-1].find('Device/StereoGain');manual(util,'ChannelMode',1);mapto(util,'Gain',14,.0630957,1)
# Use an existing native LFO preset as schema. The actual installed .amxd is referenced,
# never copied or modified. Its saved IdRefList is how Live restores the mapping.
reference=read(CORE/'Racks/Instrument Racks/Strings/Feedback Bow.adg')
lfo_template=next(d for d in reference.findall('.//MxDeviceAudioEffect') if 'LFO.amxd' in E.tostring(d.find('PatchSlot'),encoding='unicode'))
builtin=CORE.parent/'Builtin';lfo_path=builtin/'Devices/Audio Effects/LFO/Ableton Folder Info/LFO.amxd'
assert lfo_path.is_file(),lfo_path
for i in range(10):
 target_id=1000+i;setv(rack,f'MacroControls.{i}/LomId',target_id)
 lfo=copy.deepcopy(lfo_template);unmap(lfo)
 setv(lfo,'UserName',f'Evolve {names[i]}');setv(lfo,'IsFolded',True)
 setv(lfo,'PatchSlot/Value/MxDPatchRef/FileRef/Path',lfo_path)
 parameters={p.find('Name').get('Value'):p for p in lfo.findall('ParameterList/ParameterList/*')}
 for name,value in {'Depth':100,'Freq Rate':4.22948265,'Hold':0,'Jitter':20,'Offset':0,'Phase':i*10,'Re-Trigger':0,'Shape':0,'Smooth':100,'Time Mode':0}.items():manual(parameters[name],'Timeable',value)
 for name,idx,lo,hi in [('Hold',10,0,1),('Depth',11,0,100),('Smooth',12,50,100)]:mapto(parameters[name],'Timeable',idx,lo,hi)
 for ref in lfo.findall('IdRefList/IdRefList/MxDIdRef'):setv(ref,'LomId',target_id)
 blob=lfo.find('.//Blob');state=json.loads(bytes.fromhex(blob.text).rstrip(b'\x00').decode())
 state['TargetMin[7]']=[20];state['TargetMax[7]']=[80]
 blob.text=(json.dumps(state)+'\n\x00').encode().hex().upper()
 devices.append(wrap(lfo,len(devices)))
# Live stores the frequency dial in a nonlinear internal scale. This value was
# obtained by entering 0.1 Hz in Live 11.3.43 and saving the Set.
# A separate outer rack owns manual offsets: native Rand cannot write parameters
# already owned by an LFO. The inner bank retains the actual modulation targets.
outer = copy.deepcopy(g)
outer_device = outer.find('Device/InstrumentGroupDevice')
outer_devices = outer.find('BranchPresets/InstrumentBranchPreset/DevicePresets')
for child in list(outer_devices): outer_devices.remove(child)
for lom in outer_device.iter('LomId'): lom.set('Value', '0')
setv(rack, 'UserName', 'Evolving Sound')
setv(outer_device, 'UserName', 'Infisound Evolving')
setv(outer_device, 'AreDevicesVisible', True)
setv(outer_device, 'Annotation', 'Continuous ten-second sweep cycles with randomized variation. Rand changes the ten movement centers. Freeze holds movement. Wave, output, and attack stay manual.')
for i in range(16):
 setv(outer_device, f'ExcludeMacroFromRandomization.{i}', i >= 10)
 setv(outer_device, f'MacroAnnotations.{i}', 'Randomizable movement center; the inner sound continues to evolve.' if i < 10 else names[i])
 if i < 10:
  manual(outer_device, f'MacroControls.{i}', 64)
 else:
  mapto(rack, f'MacroControls.{i}', i, 0, 127)
lfopresets = [p for p in list(devices) if p.find('Device/MxDeviceAudioEffect') is not None]
for p in lfopresets: devices.remove(p)
g.set('Id', '0'); outer_devices.append(g)
for i,p in enumerate(lfopresets):
 lfo=p.find('Device/MxDeviceAudioEffect')
 offset=next(p for p in lfo.findall('ParameterList/ParameterList/*') if p.find('Name').get('Value')=='Offset')
 mapto(offset, 'Timeable', i, -35, 35)
 p.set('Id', str(i+1)); outer_devices.append(p)
root.remove(g); root.append(outer)
# Remove obsolete source metadata but retain native device identity in PatchSlot.
for parent in root.iter():
 for child in list(parent):
  if child.tag in ('SourceContext','PresetRef'):child.clear()
  elif child.tag=='LastPresetRef':child.clear();E.SubElement(child,'Value')
E.indent(root);dest=OUT/'Infisound Evolving.adg';dest.write_bytes(gzip.compress(E.tostring(root,encoding='utf-8',xml_declaration=True)))
print(dest)
# Validate mapping identities and ensure the auto-modulated graph has no enum targets.
lfos=root.findall('.//MxDeviceAudioEffect');assert len(lfos)==10
for i,lfo in enumerate(lfos):
 target=1000+i
 assert {int(r.find('LomId').get('Value')) for r in lfo.findall('IdRefList/IdRefList/*')}=={target}
 assert int(rack.find(f'MacroControls.{i}/LomId').get('Value'))==target
 p={e.find('Name').get('Value'):e for e in lfo.findall('ParameterList/ParameterList/*')}
 assert p['Shape'].find('Timeable/Manual').get('Value')=='0'
 assert float(p['Freq Rate'].find('Timeable/Manual').get('Value'))==4.22948265
 assert p['Time Mode'].find('Timeable/Manual').get('Value')=='0'
 assert p['Jitter'].find('Timeable/Manual').get('Value')=='20'
 assert int(p['Phase'].find('Timeable/Manual').get('Value'))==i*10
for bank,indexes in [(sound,[2,9,12,13,15]),(fxrack,[1,5,11])]:
 for idx in indexes:
  k=bank.find(f'MacroControls.{idx}/KeyMidi')
  assert k is None or int(k.find('NoteOrController').get('Value'))>=10
for p in root.findall('.//SampleRef/FileRef/Path'):assert Path(p.get('Value')).is_file()
for i in range(16):
 assert outer_device.find(f'ExcludeMacroFromRandomization.{i}').get('Value') == ('false' if i < 10 else 'true')
for i,lfo in enumerate(lfos):
 offset=next(p for p in lfo.findall('ParameterList/ParameterList/*') if p.find('Name').get('Value')=='Offset')
 assert int(offset.find('Timeable/KeyMidi/NoteOrController').get('Value'))==i
assert all(e.get('Value')=='0' for e in outer_device.iter('LomId'))
print('PASS: randomizable outer centers, protected safety controls, 10 continuous 0.1 Hz sweep modulators with jitter; unique restored targets; stable waveform/type/pitch/delay-time controls; all sample paths resolve.')
