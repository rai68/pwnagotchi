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
        self._state = None
        self._view = None
        self.PNG = False
        self.POSITION_X = 0
        self.POSITION_Y = 40


    def load(self, view):
        self._view = view
        config = view._config
        if view.theme:
            #load global faces
            for face_name, face_value in config.items():
                if face_name.upper() in DEFAULTS:
                    self._state.add_element_raw(face_name.upper(),Face(face_value,(config.get('position_x'),config.get('position_y')),fonts.Huge,view.FOREGROUND,png=False))
                else:
                    pass
            #add default face element
            view._state.add_element_raw('face', self._state.get_element('SLEEP'))
        
        
        
        self.POSITION_X = view.theme.theme_config['face']['pos'].get('x', None)
        self.POSITION_Y = view.theme.theme_config['face']['pos'].get('y', None)
        
        if self.POSITION_X == None or self.POSITION_Y == None:
            logging.error("!!! Theme loaded no position values for face contact theme author")
            return None
        
        tmpFaceState = {}
        for face_name, face_value in self.load_faces().items():
            tmpFaceState[face_name]= Face(face_value,(self.POSITION_X,self.POSITION_Y),fonts.Huge,view.FOREGROUND,png=True)
        
        
        self._state = State(tmpFaceState)
        
        #add default face element
        self.setFace(self._state.get_element('SLEEP'))
            
    def setFace(self, element):
        if element in DEFAULTS:
            key = value_to_key(element)
        #update element that is the face on view
        self._view._state._state['face'] = self._state.get_element(key)

    def getCurrent(self):
        #get current face object
        return self._view._state._state['face']
    
    

        
