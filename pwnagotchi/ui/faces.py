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
import pwnagotchi.ui.web as web
import pwnagotchi.ui.theme as theme
import pwnagotchi.utils as utils
from pwnagotchi.ui.components import *
from pwnagotchi.ui.state import State
from pwnagotchi.voice import Voice
    
    
DEFAULTS = {
            'LOOK_R': '( ⚆_⚆)',
            'LOOK_L': '(☉_⚆)',
            'LOOK_R_HAPPY': '( ◕‿◕)',
            'LOOK_L_HAPPY': '(◕‿◕ )',
            'SLEEP': '(⇀‿‿↼)',
            'SLEEP2': '(≖‿‿≖)',
            'AWAKE': '(◕‿‿◕)',
            'BORED': '(-__-)',
            'INTENSE': '(°▃▃°)',
            'COOL': '(⌐■_■)',
            'HAPPY': '(•‿‿•)',
            'GRATEFUL': '(^‿‿^)',
            'EXCITED': '(ᵔ◡◡ᵔ)',
            'MOTIVATED': '(☼‿‿☼)',
            'DEMOTIVATED': '(≖__≖)',
            'SMART': '(✜‿‿✜)',
            'LONELY': '(ب__ب)',
            'SAD': '(╥☁╥ )',
            'ANGRY': "(-_-')",
            'FRIEND': '(♥‿‿♥)',
            'BROKEN': '(☓‿‿☓)',
            'DEBUG': '(#__#)',
            'UPLOAD': '(1__0)',
            'UPLOAD1': '(1__1)',
            'UPLOAD2': '(0__1)'
        }
    
    
class Faces(object):
    def __init__(self):
        self._state = State(state={

            
            
        })

        self.default = DEFAULTS
        
        
        self.PNG = False
        self.POSITION_X = 0
        self.POSITION_Y = 40


    def load_from_config(self, config, view):
        self.view = view
        
        for face_name, face_value in config.items():
            self._state.add_single_raw(face_name,Face(face_value,(config.get('position_x'),config.get('position_y')),fonts.Huge,view.FOREGROUND,png=False))
            
            
        #add default face element
        view._state.add_single_raw(self._state['SLEEP'])
            
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
        view._state.add_single_raw(self._state['SLEEP'])
            
    def setFace(self, name):
        #set face current
        self.view._state[name] = self._state.get(name)
    
    def getCurrent(self):
        #get current face object
        return self.current
        
