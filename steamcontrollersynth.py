import usb.core
import usb.util

import mido
import array
import argparse

# Initialize parser
parser = argparse.ArgumentParser(
    description="""Steam Controller Synth - A MIDI to Steam Controller Synth written by @afornelas and inspired by Pila's Steam Controller Singer (Pila.fr)
    This script supports playback of midi files to the Steam Controller's Haptic touchpads with near feature parity to Pila's original program. However,
    this version does not need any third party USB drivers to be installed on later versions of Windows, and works out of the box on any Steam Controller firmware.
    This script expands on Pila's work by enabling more than one Steam Controller to be used at one time, to increase the number of haptic channels available.
    Additionally, this script can act as a synth for other MIDI devices, supporting the dynamic allocation of Steam Controller Haptic pads in real time to enable
    polyphony on the same channel when used as the output for a MIDI input device such as a keyboard.""",
    epilog="Check out more projects at afornelas.github.io"
)
parser.add_argument('-f','--file', help='MIDI File to play, if not specified, configures the Steam Controller to be a live synthesizer')
parser.add_argument('-l','--logic', default='single_voice', help='''Tunes the logic of the Steam Controller, for midi playback from a file use either
    "single_voice" or "polyphony", "single_voice" is the default and most closely matches Pila\'s original program. In this mode, the connected Steam
    Controller\'s haptic touchpads are assigned a channel (0-SC*2-1) and will play the most recent note in that channel.
    "polyphony" is a more advanced mode that allows the Steam Controllers to play multiple notes from the same channel at the same time.
    This mode is recommended for MIDI playback whenever the maximum amount of polyphony does not exceed the amount of haptic touchpads avaiable to the program.
    It is also mandatory for MIDI input to work correctly.''')
parser.add_argument('-c','--controllers', default=1, help='Number of controllers to use, automatically defaults to 1 for ease of use')
parser.add_argument('-m','--midi_input_port', help='MIDI input port to use and recieve data from, currently avaiable ports: {}'.format(str(mido.get_input_names())))

args = parser.parse_args()

# Global Variables

steam_controller_magic_period_ratio = 495483
duration_max = -1
note_stop = -1

midi_frequency = [8.1758, 8.66196, 9.17702, 9.72272, 10.3009, 10.9134, 11.5623, 12.2499, 12.9783, 13.75,
14.5676, 15.4339, 16.3516, 17.3239, 18.354, 19.4454, 20.6017, 21.8268, 23.1247, 24.4997, 25.9565, 27.5,
29.1352, 30.8677, 32.7032, 34.6478, 36.7081, 38.8909, 41.2034, 43.6535, 46.2493, 48.9994, 51.9131, 55,
58.2705, 61.7354, 65.4064, 69.2957, 73.4162, 77.7817, 82.4069, 87.3071, 92.4986, 97.9989, 103.826, 110,
116.541, 123.471, 130.813, 138.591, 146.832, 155.563, 164.814, 174.614, 184.997, 195.998, 207.652, 220,
233.082, 246.942, 261.626, 277.183, 293.665, 311.127, 329.628, 349.228, 369.994, 391.995, 415.305, 440,
466.164, 493.883, 523.251, 554.365, 587.33, 622.254, 659.255, 698.456, 739.989, 783.991, 830.609, 880,
932.328, 987.767, 1046.5, 1108.73, 1174.66, 1244.51, 1318.51, 1396.91, 1479.98, 1567.98, 1661.22, 1760,
1864.66, 1975.53, 2093, 2217.46, 2349.32, 2489.02, 2637.02, 2793.83, 2959.96, 3135.96, 3322.44, 3520, 3729.31,
3951.07, 4186.01, 4434.92, 4698.64, 4978.03, 5274.04, 5587.65, 5919.91, 6271.93, 6644.88, 7040, 7458.62,
7902.13, 8372.02, 8869.84, 9397.27, 9956.06, 10548.1, 11175.3, 11839.8, 12543.9]

# On Windows, if no backend found:
# Run 'pip install libusb'
# libusb-1.0.dll will be added to 'Python\Python3X\Lib\site-packages\libusb\_platform\_windows'
# add both contained folders (x64 and x86) to Path enviorment variable

def find_and_claim_steam_controller():
    '''
    Finds and claims a Steam Controller and returns it as a usb.core.Device object
    '''
    steam_controller = usb.core.find(idVendor=0x28DE, idProduct=0x1102)

    if steam_controller is None:
        raise ValueError('[INFO] Wired Steam Controller not found')

    try:
        usb.core.util.claim_interface(steam_controller, 2)
    except usb.core.USBError as e:
        print('[ERROR] Unable to claim interface: ' + str(e))
    
    return steam_controller

def close_steam_controller(steam_controller):
    '''Closes the steam controller usb.core.Device Object'''
    usb.core.util.release_interface(steam_controller, 2)
    steam_controller.reset()

def steam_controller_play_note(steam_controller, haptic, note, duration = duration_max):
    '''
    Plays a note on the Steam Controller

    steam_controller is a usb.core.Device object from find_and_claim_steam_controller()

    haptic is the haptic to play the note on (0: left, 1: right)

    note is the note to play (Follows MIDI standard)

    duration is the duration of the note in milliseconds (default: -1 = infinite)
    '''
    
    # data packet is a list of 64 bytes, and is described as per in-line comments

    data_packet = [0x8f,
                0x07,
                0x00, # Trackpad select : 0x01 = left, 0x00 = right
                0xff, # LSB Pulse High Duration
                0xff, # MSB Pulse High Duration
                0xff, # LSB Pulse Low Duration
                0xff, # MSB Pulse Low Duration
                0xff, # LSB Pulse repeat count
                0x04, # MSB Pulse repeat count
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
                
    if note == note_stop:
        note = 0
        duration = 0
    
    frequency = midi_frequency[note]
    period = 1/frequency
    period_command = period * steam_controller_magic_period_ratio

    repeat_count = duration/period if duration >= 0 else 0x7FFF

    # Assign variables to data packet

    data_packet[2] = haptic
    data_packet[3] = int(period_command % 256)
    data_packet[4] = int(period_command / 256)
    data_packet[5] = int(period_command % 256)
    data_packet[6] = int(period_command / 256)
    data_packet[7] = int(repeat_count % 256)
    data_packet[8] = int(repeat_count / 256)

    try:
        steam_controller.ctrl_transfer(0x21,9,0x0300,2,array.array('B',data_packet),1000)
    except usb.core.USBError as e:
        print('[ERROR] Unable to write to interface: ' + str(e))

def display_played_notes(channel, note):
    if note == note_stop:
        note_str = 'OFF'
    else:
        note_names = [" C","C#"," D","D#"," E"," F","F#"," G","G#"," A","A#"," B"]
        note_str = note_names[note % 12] + str(int(note/12)-1)
        # print(note_str)

    controller_output = '\r'
    for i in list(range(channel+1)):
        print('\r'+'\t'*(i*3) + ("LEFT Haptic {}:".format(int(i/2 + 1)) if i%2 == 0 else "RIGHT Haptic {}:".format(int((i-1)/2 +1))), end='')
    print(controller_output, end='')
    print('\r'+'\t'*(((channel)*3)+2)+note_str, end='')

def tune(controller):
    for i in range(128):
        display_played_notes(0, i)
        steam_controller_play_note(controller, 0, i)
        input('Press Enter to continue...')

def play_song(controllers,song,logic):
    port = steam_controller_mido_port(controllers,logic=logic)
    mid = mido.MidiFile(song)
    print('Now Playing:',song)
    try: 
        for msg in mid.play():
            port.send(msg)
    except KeyboardInterrupt:
        print('\nStopping...')
        port.send(mido.Message('stop'))

class steam_controller_mido_port(mido.ports.BaseOutput):
    def __init__(self, controllers, debug = False, logic = 'single_voice'):
        mido.ports.BaseOutput.__init__(self)
        self.controllers = controllers
        if type(controllers) is not list:
            self.controllers = [self.controllers]
        self.channels = len(self.controllers)*2-1
        # channel, note
        self.previous_notes = [0]* (self.channels+1)
        self.debug = debug
        self.logic = logic
        self.queue = [None]*(self.channels+1)
        
    def single_voice(self, msg):
        '''This implementation of the midi is used for Midi exports inwhere each haptic pad has
        its own unique midi channel assigned to it. In this manner it is possible to pop notes, as the missing
        note_off event can be assumed, in order to play the most recent note and not hang on a longer duration.
        However, this does not support channel polyphony, polyphony can still be achived by writing one note per
        channel, however, this it is often tedius to rewrite music, and is not recommended.'''
        if msg.channel <= self.channels:
            controller,haptic = msg.channel // 2, msg.channel % 2
            if msg.type == 'note_on':
                if msg.velocity == 0:
                    steam_controller_play_note(self.controllers[controller], haptic, note_stop)
                    display_played_notes(msg.channel, note_stop)
                else:
                    display_played_notes(msg.channel, msg.note)
                    steam_controller_play_note(self.controllers[controller], haptic, msg.note)
            elif msg.type == 'note_off':
                steam_controller_play_note(self.controllers[controller], haptic, note_stop)
                display_played_notes(msg.channel, note_stop)
    
    def polyphony(self, msg):
        '''This implementation of parsing midi data is optimized for a midi keyboard, and as such behaves as expected. However,
        it is not possible to pop old notes in order to make new notes, as expected for a synth that runs out of voices.'''
        if msg.type == 'note_on':
            if msg.velocity == 0:
                # Musescore sends its note_off events as velocity = 0
                for i in range(len(self.queue)):
                    if self.queue[i] is not None:
                        if self.queue[i]['channel'] == msg.channel and self.queue[i]['note'] == msg.note:
                            controller,haptic = i // 2, i % 2
                            steam_controller_play_note(self.controllers[controller], haptic, note_stop)
                            display_played_notes(i, note_stop)
                            self.queue[i] = None
                            break
            else:
                for i in range(len(self.queue)):
                    if self.queue[i] == None:
                        # populate index with msg metadata
                        self.queue[i] = {
                            'channel': msg.channel,
                            'note': msg.note
                        }
                        controller, haptic = i // 2, i % 2
                        steam_controller_play_note(self.controllers[controller], haptic, msg.note)
                        display_played_notes(i, msg.note)
                        break
        elif msg.type == 'note_off':
            for i in range(len(self.queue)):
                if self.queue[i] is not None:
                    if self.queue[i]['channel'] == msg.channel and self.queue[i]['note'] == msg.note:
                        controller,haptic = i // 2, i % 2
                        steam_controller_play_note(self.controllers[controller], haptic, note_stop)
                        display_played_notes(i, note_stop)
                        self.queue[i] = None
                        break
    
    def _send(self, msg):
        if msg.type == 'stop':
            for i in range(self.channels+1):
                controller,haptic = i // 2, i % 2
                steam_controller_play_note(self.controllers[controller], haptic, note_stop)

        if self.logic == 'single_voice':
            self.single_voice(msg)
        elif self.logic == 'polyphony':
            self.polyphony(msg)
        else:
            raise ValueError('Invalid logic type: ' + self.logic)

controllers = []
for i in range(int(args.controllers)):
    controllers.append(find_and_claim_steam_controller())
print('[INFO] {} Steam Controller found'.format(len(controllers)))

if args.file == None:
    if args.midi_input_port == None:
        try:
            midi_keyboard = mido.open_input(mido.get_input_names()[0])
        except IndexError:
            print('[WARNING] No midi keyboards found')
            exit()
    elif type(args.midi_input_port) == str:
        midi_keyboard = port = mido.open_input(args.midi_input_port)
    print('[READY] Listening to midi keyboard:',midi_keyboard.name)
    output_port = steam_controller_mido_port(controllers,logic='polyphony')
    for msg in midi_keyboard:
        try:
            output_port.send(msg)
        except KeyboardInterrupt:
            print('\nStopping...')
            output_port.send(mido.Message('stop'))
elif type(args.file) == str:
    play_song(controllers, args.file, args.logic)