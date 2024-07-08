import _thread
import logging
import random
import time
import os
from threading import Lock

from PIL import ImageDraw
import toml

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.faces as faces
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.ui.web as web
import pwnagotchi.ui.theme as theme
import pwnagotchi.utils as utils
from pwnagotchi.ui.components import *
from pwnagotchi.ui.state import State
from pwnagotchi.voice import Voice


#defaults for backwards compat
WHITE = 0x00 # white is actually black on jays image
BLACK = 0xFF # black is actually white on jays image

#self.FOREGROUND is the main color
#self.BACKGROUNDGROUND is the 2ndary color, used for background

#1 (1-bit pixels, black and white, stored with one pixel per byte)
BACKGROUND_1 = 0
FOREGROUND_1 = 1

#L (8-bit pixels, grayscale)
BACKGROUND_L = 0
FOREGROUND_L = 255

#BGR;16 (5,6,5 bits, for 65k color)
BACKGROUND_BGR_16 = (0,0,0)
FOREGROUND_BGR_16 = (31,63,31)

#RGB;18 (6,6,6 bits, for 262k color)
BACKGROUND_BGR_18 = (0,0,0)
FOREGROUND_BGR_18 = (63,63,63)

#RGB (3x8-bit pixels, true color)
BACKGROUND_RGB = (0,0,0)
FOREGROUND_RGB = (255,255,255)


ROOT = None

# Unused display colors so far
#P (8-bit pixels, mapped to any other mode using a color palette)
#RGBA (4x8-bit pixels, true color with transparency mask)
#CMYK (4x8-bit pixels, color separation)
#YCbCr (3x8-bit pixels, color video format)




class View(object):
    def __init__(self, config, impl, state=None):
        global ROOT
        self.invert = 0
        
        if config['ui'].get('invert', False):
            if self.mode != "1":
                logging.debug("display does not support inverting (yet?): " + str(config['ui']['invert']))
            else:
                logging.debug("display inverting: " + str(config['ui']['invert']))
                self.invert = 1
                tmp = self.BACKGROUND 
                self.BACKGROUND = self.FOREGROUND
                self.FOREGROUND = tmp
        
        
        
        #values/code for display color mode    
        self.theme = None
        self.mode = '1' # 1 = (1-bit pixels, black and white, stored with one pixel per byte)
        if hasattr(impl, 'mode'):
            self.mode = impl.mode
            
        
        
        match self.mode:
            case '1':
                self.BACKGROUND = BACKGROUND_1
                self.FOREGROUND = FOREGROUND_1
                # do stuff is color mode is 1 when View object is created. 
            case 'L':
                self.BACKGROUND =  BACKGROUND_L # black 0 to 255
                self.FOREGROUND = FOREGROUND_L
                # do stuff is color mode is L when View object is created.
            case 'P':
                pass
                # do stuff is color mode is P when View object is created.
            case 'BGR;16':
                self.BACKGROUND = BACKGROUND_BGR_16 #black tuple
                self.FOREGROUND = FOREGROUND_BGR_16 #white tuple
            case 'RGB':
                self.BACKGROUND = BACKGROUND_RGB #black tuple
                self.FOREGROUND = FOREGROUND_RGB #white tuple
                # do stuff is color mode is RGB when View object is created.
            case 'RGBA':
                # do stuff is color mode is RGBA when View object is created.
                pass
            case 'CMYK':
                # do stuff is color mode is CMYK when View object is created.
                pass
            case 'YCbCr':
                # do stuff is color mode is YCbCr when View object is created.
                pass
            case _:
                # do stuff when color mode doesnt exist for display
                self.BACKGROUND = BACKGROUND_1
                self.FOREGROUND = FOREGROUND_1
            
            

        
        
        #if theme configured, theme load all things from file, create a state object then give it to view
        if self._config['ui'].get('theme', False) not in (False,""):
            #return if no theme to load because ui.theme = "" or False
            self.theme = theme.Theme(config, self.mode, impl._layout['width'],impl._layout['height']).load_theme()
            
        self._agent = None
        self._render_cbs = []
        self._config = config
        self._canvas = None
        self._frozen = False
        self._lock = Lock()
        self._voice = Voice(lang=config['main']['lang'])
        self._implementation = impl
        self._layout = impl.layout() # ui layout in display config, should be defaults if no theme or config
        self._width = self._layout['width']
        self._height = self._layout['height']
        self._ori = None #this actually isnt supported on like 90% of displays lol, its not exposed anywhere
        
        self._state = None
        
        if self.theme is None:
            self._state = State()
            
            defaultElems = {
            'channel': LabeledValue(color=self.FOREGROUND, label='CH', value='00', position=self._layout['channel'],
                                    label_font=fonts.Bold,
                                    text_font=fonts.Medium),
            'aps': LabeledValue(color=self.FOREGROUND, label='APS', value='0 (00)', position=self._layout['aps'],
                                label_font=fonts.Bold,
                                text_font=fonts.Medium),

            'uptime': LabeledValue(color=self.FOREGROUND, label='UP', value='00:00:00', position=self._layout['uptime'],
                                   label_font=fonts.Bold,
                                   text_font=fonts.Medium),

            'line1': Line(self._layout['line1'], color=self.FOREGROUND),
            'line2': Line(self._layout['line2'], color=self.FOREGROUND),
        
            #gets this face compoant from faces object now 
            #'face': Text(value=faces.SLEEP, position=(config['ui']['faces']['position_x'], config['ui']['faces']['position_y']), color=self.FOREGROUND, font=fonts.Huge, png=config['ui']['faces']['png']),

            # 'friend_face': Text(value=None, position=self._layout['friend_face'], font=fonts.Bold, color=self.FOREGROUND),
            'friend_name': Text(value=None, position=self._layout['friend_face'], font=fonts.BoldSmall, color=self.FOREGROUND),

            'name': Text(value='%s>' % 'pwnagotchi', position=self._layout['name'], color=self.FOREGROUND, font=fonts.Bold),

            'status': Text(value=self._voice.default(),
                           position=self._layout['status']['pos'],
                           color=self.FOREGROUND,
                           font=self._layout['status']['font'],
                           wrap=True,
                           # the current maximum number of characters per line, assuming each character is 6 pixels wide
                           max_length=self._layout['status']['max']),

            'shakes': LabeledValue(label='PWND ', value='0 (00)', color=self.FOREGROUND,
                                   position=self._layout['shakes'], label_font=fonts.Bold,
                                   text_font=fonts.Medium),
            'mode': Text(value='AUTO', position=self._layout['mode'],
                         font=fonts.Bold, color=self.FOREGROUND),
            }
            
        elif self.theme is not None:
            #reference theme state to view state
            self._state = self.theme._state
        
        #load 
        self.faces = faces.Faces(self)
        

        plugins.on('ui_setup', self)

        if config['ui']['fps'] > 0.0:
            _thread.start_new_thread(self._refresh_handler, ())
            self._ignore_changes = ()
        else:
            logging.warning("ui.fps is 0, the display will only update for major changes")
            self._ignore_changes = ('uptime', 'name')

        ROOT = self

    def set_agent(self, agent):
        self._agent = agent

    def has_element(self, key):
        self._state.has_element(key)

    def add_element(self, key, elem):
        # this is the ui invert code, its being removed in favour for FOREGROUND/BACKGROUND configs
        #if self.invert is 1 and hasattr(elem, 'color'):
        #    if elem.color == 0xff: 
        #        elem.color = 0x00
        #    elif elem.color == 0x00:
        #        elem.color = 0xff
        
        # sets color to foreground overwriting everything that sets a color.
        #if ui element has a color set in config/theme use that instead
        elem.color = self.FOREGROUND
        self._state.add_element(key, elem)

    def remove_element(self, key):
        self._state.remove_element(key)

    def width(self):
        return self._width

    def height(self):
        return self._height

    def on_state_change(self, key, cb):
        self._state.add_listener(key, cb)

    def on_render(self, cb):
        if cb not in self._render_cbs:
            self._render_cbs.append(cb)

    def _refresh_handler(self):
        delay = 1.0 / self._config['ui']['fps']
        while True:
            try:
                name = self._state.get('name')
                self.set('name', name.rstrip('█').strip() if '█' in name else (name + ' █'))
                self.update()
            except Exception as e:
                logging.warning("non fatal error while updating view: %s" % e)

            time.sleep(delay)

    def set(self, key, value):
        if key == 'face':
            self.faces.setFace(key, value)
        else:
            self._state.set(key, value)
        
    def set_label(self, key, value):
        self._state.set_label(key, value)

    def get(self, key):
        return self._state.get(key)

    def on_starting(self):
        self.set('status', self._voice.on_starting() + ("\n(v%s)" % pwnagotchi.__version__))
        self.set('face', faces.AWAKE)
        self.update()

    def on_ai_ready(self):
        self.set('mode', '  AI')
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_ai_ready())
        self.update()

    def on_manual_mode(self, last_session):
        self.set('mode', 'MANU')
        self.set('face', faces.SAD if (last_session.epochs > 3 and last_session.handshakes == 0) else faces.HAPPY)
        self.set('status', self._voice.on_last_session_data(last_session))
        self.set('epoch', "%04d" % last_session.epochs)
        self.set('uptime', last_session.duration)
        self.set('channel', '-')
        self.set('aps', "%d" % last_session.associated)
        self.set('shakes', '%d (%s)' % (last_session.handshakes, utils.total_unique_handshakes(self._config['bettercap']['handshakes'])))
        self.set_closest_peer(last_session.last_peer, last_session.peers)
        self.update()

    def is_normal(self):
        return self._state.get('face') not in (
            faces.INTENSE,
            faces.COOL,
            faces.BORED,
            faces.HAPPY,
            faces.EXCITED,
            faces.MOTIVATED,
            faces.DEMOTIVATED,
            faces.SMART,
            faces.SAD,
            faces.LONELY)

    def on_keys_generation(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_keys_generation())
        self.update()

    def on_normal(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_normal())
        self.update()

    def set_closest_peer(self, peer, num_total):
        if peer is None:
            self.set('friend_face', None)
            self.set('friend_name', None)
        else:
            # ref. https://www.metageek.com/training/resources/understanding-rssi-2.html
            if peer.rssi >= -67:
                num_bars = 4
            elif peer.rssi >= -70:
                num_bars = 3
            elif peer.rssi >= -80:
                num_bars = 2
            else:
                num_bars = 1

            name = '▌' * num_bars
            name += '│' * (4 - num_bars)
            name += ' %s %d (%d)' % (peer.name(), peer.pwnd_run(), peer.pwnd_total())

            if num_total > 1:
                if num_total > 9000:
                    name += ' of over 9000'
                else:
                    name += ' of %d' % num_total

            self.set('friend_face', peer.face())
            self.set('friend_name', name)
        self.update()

    def on_new_peer(self, peer):
        face = ''
        # first time they met, neutral mood
        if peer.first_encounter():
            face = random.choice((faces.AWAKE, faces.COOL))
        # a good friend, positive expression
        elif peer.is_good_friend(self._config):
            face = random.choice((faces.MOTIVATED, faces.FRIEND, faces.HAPPY))
        # normal friend, neutral-positive
        else:
            face = random.choice((faces.EXCITED, faces.HAPPY, faces.SMART))

        self.set('face', face)
        self.set('status', self._voice.on_new_peer(peer))
        self.update()
        time.sleep(3)

    def on_lost_peer(self, peer):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lost_peer(peer))
        self.update()

    def on_free_channel(self, channel):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_free_channel(channel))
        self.update()

    def on_reading_logs(self, lines_so_far=0):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_reading_logs(lines_so_far))
        self.update()

    def wait(self, secs, sleeping=True):
        was_normal = self.is_normal()
        part = secs/10.0

        for step in range(0, 10):
            # if we weren't in a normal state before going
            # to sleep, keep that face and status on for
            # a while, otherwise the sleep animation will
            # always override any minor state change before it
            if was_normal or step > 5:
                if sleeping:
                    if secs > 1:
                        self.set('face', faces.SLEEP)
                        self.set('status', self._voice.on_napping(int(secs)))

                    else:
                        self.set('face', faces.SLEEP2)
                        self.set('status', self._voice.on_awakening())
                else:
                    self.set('status', self._voice.on_waiting(int(secs)))

                    good_mood = self._agent.in_good_mood()
                    if step % 2 == 0:
                        self.set('face', faces.LOOK_R_HAPPY if good_mood else faces.LOOK_R)
                    else:
                        self.set('face', faces.LOOK_L_HAPPY if good_mood else faces.LOOK_L)

            time.sleep(part)
            secs -= part

        self.on_normal()

    def on_shutdown(self):
        self.set('face', faces.SLEEP)
        self.set('status', self._voice.on_shutdown())
        self.update(force=True)
        self._frozen = True

    def on_bored(self):
        self.set('face', faces.BORED)
        self.set('status', self._voice.on_bored())
        self.update()

    def on_sad(self):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_sad())
        self.update()

    def on_angry(self):
        self.set('face', faces.ANGRY)
        self.set('status', self._voice.on_angry())
        self.update()

    def on_motivated(self, reward):
        self.set('face', faces.MOTIVATED)
        self.set('status', self._voice.on_motivated(reward))
        self.update()

    def on_demotivated(self, reward):
        self.set('face', faces.DEMOTIVATED)
        self.set('status', self._voice.on_demotivated(reward))
        self.update()

    def on_excited(self):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_excited())
        self.update()

    def on_assoc(self, ap):
        self.set('face', faces.INTENSE)
        self.set('status', self._voice.on_assoc(ap))
        self.update()

    def on_deauth(self, sta):
        self.set('face', faces.COOL)
        self.set('status', self._voice.on_deauth(sta))
        self.update()

    def on_miss(self, who):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_miss(who))
        self.update()

    def on_grateful(self):
        self.set('face', faces.GRATEFUL)
        self.set('status', self._voice.on_grateful())
        self.update()

    def on_lonely(self):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lonely())
        self.update()

    def on_handshakes(self, new_shakes):
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_handshakes(new_shakes))
        self.update()

    def on_unread_messages(self, count, total):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_unread_messages(count, total))
        self.update()
        time.sleep(5.0)

    def on_uploading(self, to):
        self.set('face', random.choice((faces.UPLOAD, faces.UPLOAD1, faces.UPLOAD2)))
        self.set('status', self._voice.on_uploading(to))
        self.update(force=True)

    def on_rebooting(self):
        self.set('face', faces.BROKEN)
        self.set('status', self._voice.on_rebooting())
        self.update()

    def on_custom(self, text):
        self.set('face', faces.DEBUG)
        self.set('status', self._voice.custom(text))
        self.update()

    def update(self, force=False, new_data={}):
        for key, val in new_data.items():
            self.set(key, val)

        with self._lock:
            if self._frozen:
                return

            state = self._state
            changes = state.changes(ignore=self._ignore_changes)
            if force or len(changes):
                self._canvas = Image.new(self.mode, (self._width, self._height), self.BACKGROUND) #sets background to BACKGROUND color
                drawer = ImageDraw.Draw(self._canvas, self.mode)
                
                # Draw an image background here if it exists and is a drawable component
                if 'background' in state._state and isinstance(state._state['background'], ImageBackground):
                    self._state['background'].draw(self._canvas, drawer)
                    

                plugins.on('ui_update', self)

                for key, lv in state.items():
                    #lv is a ui componant from States
                    #random colors for fun
                    if self._config['ui'].get('randomise', False):
                        if key != 'background':
                            if self.mode == "RGB" :
                                lv.color = (random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
                            elif self.mode == "BGR;16":
                                lv.color = (random.randint(0, 31),random.randint(0, 63),random.randint(0, 31))
                        
                    #draw final LV if not background because its drawn above
                    if isinstance(lv, ImageBackground):
                        pass
                    else:
                        lv.draw(self._canvas, drawer)

                web.update_frame(self._canvas)

                for cb in self._render_cbs:
                    cb(self._canvas)

                self._state.reset()
