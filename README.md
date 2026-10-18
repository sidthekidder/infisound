# Infisound

A programmable Ableton Live instrument rack for exploring randomized synth sounds. Python builds native `.adg` racks and generates their waveform samples using only the standard library.

## Racks

**Infisound** provides eight waveform timbres and 16 macros for tone, envelopes, stereo spread, drive, modulation, delay, and reverb. Volume is excluded from randomization.

**Infisound Expanded** provides 16 waveform timbres and a single top-level **Rand** button. Sixteen master macros drive 32 sound and effects controls in pairs. Output stays fixed at −6 dB after a limiter. The waveform chains share one effects chain.

The expanded controls include filter type and resonance, separate release, filter modulation, LFO speed and shape, vibrato, velocity response, glide, distortion curves, chorus, phaser/flanger/doubler, bitcrushing, stereo auto-pan, delay feedback, and reverb damping.

**Infisound Evolving** adds ten phase-staggered sine LFO lanes with 20% jitter and smoothing, running at 0.1 Hz (a roughly ten-second cycle). It is designed for held notes and evolving textures. Waveform, effect types, pitch, delay time, and output are kept out of automatic modulation.

**Infisound Transform** emphasizes large changes in timbre. Two nested crossfade axes blend four continuously triggered sources: Sine, Saw, Metal, and Vowel. Eleven LFOs move the blend, filter, envelopes, and effects.

## Requirements

- Python 3.9 or later; no external Python packages.
- A local Ableton Live 11 installation with its Core Library.
- The device presets referenced by the builders. Their filenames and structure are version-dependent.

The base rack and the earlier two-bank expanded rack loaded in Live 11.3.43 Intro. The latest single-Rand version passes structural validation, but its final Live reload and complete audio behavior have not yet been verified.

## Build

On macOS with Live 11 Intro in its default application location:

```sh
python3 tools/build_rack.py
python3 tools/build_expanded.py
python3 tools/build_evolving.py
python3 tools/build_transform.py
```

For another installation, set the Core Library location first:

```sh
export INFISOUND_CORE_LIBRARY='/path/to/Ableton/Core Library'
```

Optionally set `INFISOUND_OUTPUT_DIR` to an absolute output directory before running the builders. Otherwise output goes to `dist/`:

```text
dist/
  Infisound/
    Infisound.adg
    Samples/
  Infisound Expanded/
    Infisound Expanded.adg
    Samples/
  Infisound Evolving/
    Infisound Evolving.adg
```

Build in the order shown above. Evolving uses Expanded and its generated samples; keep both output folders. Build the base rack before the expanded rack; the expanded builder uses its device structure. Generated files are excluded from Git because their sample references contain absolute local paths. Keep the generated folders in place, or use Live's **Collect All and Save** when moving a Set.

## Play

Load the generated `.adg` on a MIDI track. Play notes and press the top-level **Rand** button. In Expanded, each master macro controls one Sound macro and one FX macro. This gives 16 independent random values, not 32 independent draws. The inner bank macros are mapped to the outer rack.

Right-click a master macro and choose **Exclude Macro from Randomization** to preserve its entire pair. Use the outer rack's **Macro Variations** to capture and recall complete combinations.

| Master macro | Sound control | FX control |
| --- | --- | --- |
| Tone | Cutoff | Reverb damping, inverted |
| Contour | Filter envelope | Phase effect type |
| Character | Waveform | Distortion curve |
| Attack + Air | Attack | Chorus rate |
| Body | Sustain | Chorus mix |
| Decay + Echo | Decay | Delay mix |
| Release + Space | Release | Reverb size and decay |
| Width + Pan | Spread | Auto-pan depth |
| Reso + Phase | Resonance | Phaser mix |
| Filter + Room | Filter type | Reverb mix |
| Motion + Crush | Filter modulation | Bitcrush mix |
| Movement Rate | LFO rate | Auto-pan rate |
| Motion Shape | LFO shape | Crush sample rate, inverted |
| Vibrato + Drive | Vibrato | Distortion drive |
| Touch + Feedback | Velocity response | Delay feedback |
| Glide + Echo | Glide time | Delay time |

Wave selects discrete timbres: Sine, Triangle, Saw, Square, Pulse, Hollow, Organ, Glass, Reed, Bell, Soft Buzz, Narrow Pulse, Octave Stack, Fifths, Metal, and Vowel. Each occupies eight consecutive values from 0 to 127.

## Evolving controls

Load **Infisound Evolving.adg** onto a MIDI track and play or hold notes. The outer rack sets the movement centers; the gray macros inside **Evolving Sound** show the changing values. The inner rack is visible by default.

- Press the outer **Rand** button to randomize the centers for Tone, Texture, Space, Motion, Width, Resonance, Echo, Grain, Brightness, and Pan Speed. These outer knobs stay still between presses; ten phase-staggered LFOs with randomized variation continuously move the corresponding inner controls. Rand changes offsets immediately; it does not trigger a synchronized ten-second morph.
- **Freeze**: turn fully up to hold the modulation outputs; return to zero to resume.
- **Depth**: reduce for subtler movement around the midpoint. Changing depth can shift the current value.
- **Smooth**: controls the native LFO smoothing, from 50% to 100%; it is not a duration in seconds.
- **Wave**, **Output**, and **Attack** remain manual. The last six controls, including Freeze, Depth, and Smooth, are excluded from Rand.

This uses the built-in Ableton LFO included with Live 11 Intro; it does not require a custom Max for Live device. The LFO file is referenced from the installed application. The rack uses continuous sine sweeps with 20% jitter for randomized variation. Each cycle is approximately ten seconds. It does not choose an independent random patch every ten seconds or interpolate between stored presets. Random-wave mode was tested and rejected because it glided briefly and then held; sine mode keeps the motion flowing.

## Transform controls

Build after Evolving and load `dist/Infisound Transform/Infisound Transform.adg`. Keep the Expanded sample folder in place.

- **Morph** blends the Sine/Saw pair with the Metal/Vowel pair. **Material** crossfades within each pair. All four voices have full MIDI selector ranges, with complementary audio fades, so held notes can change timbre.
- **Tone** spans a much wider filter range. **Texture** adds stronger drive and chorus; **Grain** reaches deeper bitcrushing.
- **Envelope** varies attack, sustain, and decay. **Space** also changes release. Envelope changes affect note articulation and are most obvious with new notes. **Env Depth** remains manual.
- The outer knobs are movement centers; **Moving Sound** shows actual changing values. **Rand** changes the first ten centers plus Morph. Freeze, Depth, Smooth, Output, and Env Depth stay protected.
- Depth defaults to maximum. Two crossfade stages and additional headroom help contain the combined voices, but this is not loudness-normalized; timbres can differ in perceived level.

Transform checks four voices, full MIDI zones, complementary fade endpoints, eleven LFOs, sample paths, and output protection. The preset loaded in Live 11.3.43 Intro and both morph controls were observed moving. Listening and held-note crossfade verification are still required.

## Implementation and validation

An `.adg` is a gzip-compressed XML preset. The builders read device schemas from the installed Core Library, assemble rack chains and macro mappings, generate waveform WAVs, and write the compressed preset. Ableton's native devices perform the audio processing.

The expanded builder asserts macro coverage, waveform selection coverage without gaps or overlaps, sample-file existence, a shared reverb instance, and an unmapped final output gain. These checks do not replace loading and listening in Live.

The evolving builder checks all ten LFO rates, sine mode, restored target identities, sample paths, and exclusion of discrete switches from automatic mapping. The first version incorrectly wrote the frequency dial as 0.1, which Live displayed near 0 Hz. The corrected builder uses 4.22948265, measured by entering 0.1 Hz in Live 11.3.43 and saving the Set. A separate outer rack owns the randomizable LFO offsets, because native Rand cannot write LFO-owned macros. The repaired preset loads in Live and its outer Rand has been verified to change the first ten controls while preserving the final six. The corrected Random-wave version continued changing across multiple cycles, but its smoothing left long holds. The sine-with-jitter version loaded in Live and its inner macro values were observed moving between screenshots. The user verified Rand on the repaired outer-rack architecture. Freeze still needs a complete pause/resume check, and exhaustive listening tests remain outstanding.

Remaining limitations:

- The preset format is version-dependent and not a stable public authoring API.
- High pitches can produce aliasing from the sampled waveforms.
- Random settings are bounded but not loudness-normalized or guaranteed to sound useful.
- Global randomization deliberately couples sound and FX parameters.
- Exhaustive listening and parameter-extreme checks remain to be done.

## References

- [Ableton Macro and Variations FAQ](https://help.ableton.com/hc/en-us/articles/360019103480-Macros-and-Variations-FAQ)
- [Built-in Max for Live devices in Live 11 Intro and Standard](https://help.ableton.com/hc/en-us/articles/360019145319-Max-for-Live-Devices-in-Live-11-Intro-and-Standard)
- [Live 11 LFO reference](https://www.ableton.com/en/live-manual/11/max-for-live-devices/)
- [Live 11 audio effect reference](https://www.ableton.com/en/live-manual/11/live-audio-effect-reference/)

Ableton Live and its Core Library are required separately. This repository does not include the installed Core Library or third-party plugins.
