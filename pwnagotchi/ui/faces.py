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
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.ui.faces as faces
import pwnagotchi.ui.web as web
import pwnagotchi.ui.theme as theme
import pwnagotchi.utils as utils
from pwnagotchi.ui.components import *
from pwnagotchi.ui.state import State
from pwnagotchi.voice import Voice
    
    
LOOK_R = '( ⚆_⚆)'
LOOK_L = '(☉_⚆)'
LOOK_R_HAPPY = '( ◕‿◕)'
LOOK_L_HAPPY = '(◕‿◕ )'
SLEEP = '(⇀‿‿↼)'
SLEEP2 = '(≖‿‿≖)'
AWAKE = '(◕‿‿◕)'
BORED = '(-__-)'
INTENSE = '(°▃▃°)'
COOL = '(⌐■_■)'
HAPPY = '(•‿‿•)'
GRATEFUL = '(^‿‿^)'
EXCITED = '(ᵔ◡◡ᵔ)'
MOTIVATED = '(☼‿‿☼)'
DEMOTIVATED = '(≖__≖)'
SMART = '(✜‿‿✜)'
LONELY = '(ب__ب)'
SAD = '(╥☁╥ )'
ANGRY = "(-_-')"
FRIEND = '(♥‿‿♥)'
BROKEN = '(☓‿‿☓)'
DEBUG = '(#__#)'
UPLOAD = '(1__0)'
UPLOAD1 = '(1__1)'
UPLOAD2 = '(0__1)'

DEFAULTS = (
    'LOOK_R', 'LOOK_L', 'LOOK_R_HAPPY', 'LOOK_L_HAPPY', 'SLEEP', 'SLEEP2', 'AWAKE', 'BORED',
    'INTENSE', 'COOL', 'HAPPY', 'GRATEFUL', 'EXCITED', 'MOTIVATED', 'DEMOTIVATED', 'SMART',
    'LONELY', 'SAD', 'ANGRY', 'FRIEND', 'BROKEN', 'DEBUG', 'UPLOAD', 'UPLOAD1', 'UPLOAD2'
)

def value_to_key(value):
    for key, val in globals().items():
        if val == value:
            return key
    return None
    
    
class Faces():
    def __init__(self):
        self._state = State(state={})
        
        self.PNG = False
        self.POSITION_X = 0
        self.POSITION_Y = 40


    def load_from_config(self, config, view):
        self.view = view
        
        #load global faces
        for face_name, face_value in config.items():
            if face_name.upper() in DEFAULTS:
                self._state.add_single_raw(face_name.upper(),Face(face_value,(config.get('position_x'),config.get('position_y')),fonts.Huge,view.FOREGROUND,png=False))
            else:
                pass
        #add default face element
        view._state.add_single_raw('face', self._state.get_element('SLEEP'))
            
    def load_from_theme(self, themeObj, view):
        self.view = view
        fx = themeObj.theme_config['face']['pos'].get('x', None)
        fy = themeObj.theme_config['face']['pos'].get('y', None)
        
        if self.POSITION_X == None or self.POSITION_Y == None:
            logging.error("!!! Theme loaded no position values contact theme author")
            
        for face_name, face_value in themeObj.get_faces_from_config().items():
            self._state.add_single_raw(face_name,Face(face_value,(fx,fy)),fonts.Huge,view.FOREGROUND,png=True)
        
        #load from theme and create all state face elements in memory so its faster
        
        #add default face element
        view._state.add_single_raw('face', self._state.get_element('SLEEP'))
            
    def setFace(self, name):
        #set face current
        self.view._state._state['face'] = self._state.get_element(name)

    def getCurrent(self):
        #get current face object
        return self.current
        
