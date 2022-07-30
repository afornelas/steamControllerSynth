# steamControllerSynth
>Turning Valve's Steam Controller into a fully functional Synth, compatible with MIDI files and input devices with full polyphony

Continuing off of [Pila's](https://gitlab.com/Pilatomic/SteamControllerSinger) work, steamControllerSynth expands and enables the playback of MIDI data from both MIDI files and input devices. Instead of being limited to one voice per channel, and two total channels, this script implements a dynamically allocating queue in order to fully saturate all haptic motors enabling full polyphony for every MIDI channel, limited only by the amount of Steam Controllers avaiable.

## Prerequisites

This script relies on a Python 3+ installation and the following dependecies:

```bash
pip install mido
pip install pyusb
```

### Windows

Unfortuntately, Windows does not have an easy way to install libusb unlike Unix based operating systems. If libusb is not already present you will have to do this:

1. pip install pyusb
2. pip install libusb
3. libusb-1.0.dll will be automatically added to:

PYTHON_DIR\Lib\site-packages\libusb\_platform\_windows\x64
and
PYTHON_DIR\Lib\site-packages\libusb\_platform\_windows\x32

For example in my case, my PYTHON_DIR that has my \Lib\ folder is C:\Users\adria\AppData\Local\Programs\Python\Python39\

Now add those paths (the full path) to Windows Path and restart your terminal.

[Original Solution](https://stackoverflow.com/a/68064311)

[More resources on adding to Windows Path](https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/)

### Linux

If libusb is not already present on your device, you can install via the following command on debian based distributions.

```bash
sudo apt install libusb-1.0-0-dev
```

## Usage

steamControllerSynth has various different modes it can be used in:

### Synth

This is the default mode, and the primary reason I wrote this script.

The following command claims a Steam Controller interface on the first steam controller avaiable and then binds it to the default MIDI input port on the host computer. Through this, the script can interpret MIDI data from a keyboard and send it to the Steam Controller in order to act as a live synthesizer.

```bash
python steamcontrollersynth.py
```

### File Playback

Just as Pila's SteamControllerSinger, steamControllerSynth can also playback MIDI files on the Steam Controller's haptic motors. In order to specify a file to playback utilize the -f or --file argument

```bash
py steamcontrollersynth.py -f '.\test.mid'
```

### Miscellaneous Options

**Backend logic**

Logic backends can be changed via the -l or --logic argument.

- single_voice - Default for file playback, most closely matches Pila's original implementation. Every haptic touchpad is assigned a MIDI channel, and it plays the most recent note in the channel. This supports up to 16 single-voice MIDI channels. (8 Steam Controllers)
- polyphony - Mandatory for live synth, every haptic touchpad is included in a dynamically allocating queue that scales with Steam Controller to enable single channel polyphony in addition to pulling midi data from all channels. Recommended for best quality when more haptic touchpads are present than maximum polyphony.

```bash
py steamcontrollersynth.py -f 'test.mid' -m single_voice
```

```bash
py steamcontrollersynth.py -f 'test.mid' -m polyphony
```

**Controllers**

The number of controllers can be controlled via the -c --controllers argument.

Default amount of controllers is 1, to address the most common use case, but this can be overridden in order to make use of additional controllers. (As of right now untested, pending arrival of Steam Controllers)

Two Controller MIDI Synth:
```bash
py steamcontrollersynth.py -c 2
```

**Midi Input**

In order to use a different MIDI input port apart from the default, you can specify which to use with the -m -midi_input_port argument.

```bash
py steamcontrollersynth.py -m 'USB MIDI Controller 0'
```

The list of aviable MIDI input ports is avaiable within the help section.

**Help**

Additional bundled help is avaiable through the following command:

```bash
py steamcontrollersynth.py -h
```
