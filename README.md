# Infisound

A programmable Ableton Live instrument rack for exploring randomized synth sounds. Python builds native `.adg` racks and generates their waveform samples using only the standard library.

## Racks

**Infisound** provides eight waveform timbres and 16 macros for tone, envelopes, stereo spread, drive, modulation, delay, and reverb. Volume is excluded from randomization.

**Infisound Expanded** provides 16 waveform timbres and a single top-level **Rand** button. Sixteen master macros drive 32 sound and effects controls in pairs. Output stays fixed at −6 dB after a limiter. The waveform chains share one effects chain.

The expanded controls include filter type and resonance, separate release, filter modulation, LFO speed and shape, vibrato, velocity response, glide, distortion curves, chorus, phaser/flanger/doubler, bitcrushing, stereo auto-pan, delay feedback, and reverb damping.

**Infisound Evolving** adds ten independent, smoothed random LFO lanes running at 0.1 Hz (a roughly ten-second cycle). It is designed for held notes and evolving textures. Waveform, effect types, pitch, delay time, and output are kept out of automatic modulation.

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

Load **Infisound Evolving.adg** onto a MIDI track and play or hold notes. Its ten sound macros are driven automatically, without pressing Rand:

- Tone, Texture, Space, Motion, Width, Resonance, Echo, Grain, Brightness, and Pan Speed move independently.
- **Freeze**: turn fully up to hold the modulation outputs; return to zero to resume.
- **Depth**: reduce for subtler movement around the midpoint. Changing depth can shift the current value.
- **Smooth**: controls the native LFO smoothing, from 50% to 100%; it is not a duration in seconds.
- **Wave**, **Output**, and **Attack** remain manual. All macros are excluded from Rand in this variant.

This uses the built-in Ableton LFO included with Live 11 Intro; it does not require a custom Max for Live device. The LFO file is referenced from the installed application. The rack uses independent random modulation with smoothing, rather than coordinated preset-to-preset interpolation: the 0.1 Hz cycle is approximately ten seconds, and smoothing can extend the transition.

## Implementation and validation

An `.adg` is a gzip-compressed XML preset. The builders read device schemas from the installed Core Library, assemble rack chains and macro mappings, generate waveform WAVs, and write the compressed preset. Ableton's native devices perform the audio processing.

The expanded builder asserts macro coverage, waveform selection coverage without gaps or overlaps, sample-file existence, a shared reverb instance, and an unmapped final output gain. These checks do not replace loading and listening in Live.

The evolving builder checks all ten LFO rates, Random mode, restored target identities, sample paths, and exclusion of discrete switches from automatic mapping. Live received the generated rack during testing, but the app-control connection timed out before the loaded UI could be inspected. Runtime verification is still pending; structural checks alone do not prove that Live restores the mappings or that Freeze behaves correctly.

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
