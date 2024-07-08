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
import pwnagotchi.utils as utils
from pwnagotchi.ui.components import *
from pwnagotchi.ui.state import State
from pwnagotchi.voice import Voice

#to do 

#use fancygotchi configs they should be fine to embed


class Theme():
    def __init__(self, config, color, width, height, ori="h"):
        self._config = config
        self._state = None
        self.display = {}
        self.display['_height'] = height
        self.display['_width'] = width
        self.display['colormode'] = color
        self.display['_ori'] = ori
        self.found = False
        self.theme_config = None
        self._loadedTheme_root = None
            
    def load_theme(self):
        #load theme
        endTheme = None
        to_load = self._config['ui'].get('theme', False)
        if to_load == False or to_load == "":
            #return if no theme to load because ui.theme = "" or False
            return endTheme
        
        logging.debug("Loading theme: " + to_load)
        
        #make theme directory list
        themes_dirs = []
        themes_dirs.extend(self._config.get('custom_themes'), ["/etc/pwnagotchi/themes"])
        
        themes = []
        for index, directory in enumerate(themes_dirs):
            for dirs in os.walk(directory):
                #load theme config from to_load name
                if dirs == to_load:
                    logging.debug("Found theme type in theme dirs")
                    try:
                                                # e.g /etc/pwnagotchi/themes/pika/pika.toml
                        #load them config
                        self.theme_config = toml.load(os.path.join(directory, dirs, to_load + ".toml"))
                        lookfor = [self._width, self._height,self._ori]
                        #get sizes supported theme sizes
                        for size in self.theme_config.get('sizes',[]):
                            if size[0] == self._width and size[1] == self._width and self._ori in size[2]:
                                self.Found = True #found theme for display
                                logging.info("Theme found for display parameters")
                                self._loadedTheme_root = os.path.join(directory, dirs) # e.g #/etc/pwnagotchi/themes/THEMENAME/
                                logging.info("Loading: " + self._loadedTheme_root)
                                
                                break
                        break
                    except Exception as e:
                        #error finding theme return None to load default
                        logging.error("Theme could not be found!")
                        return None
                    
        if not self.Found:
            #error finding theme return None to load default
            logging.error("Theme could not be found!")
            return None
                    
        self._state = State()
        
        #process background                                            width,                 height,                colormode,              orientation
        self._state.add_raw(ImageBackground(self.get_background(self.display._width, self.display._height,self.self.display.colormode, self.display._ori)))

        return self
        
        
    def get_background(self,size_x,size_y,colormode, ori):
        # Determine the directory to search based on the 'bg' parameter
        dir_to_search = os.path.join(self._loadedTheme_root, self.theme_config['background'].get('dir', ''))
        filename = f"background-{size_x}-{size_y}-{colormode}-{ori}.png"


        # Construct the filename based on the input parameters
        
        # Construct the full file path
        file_path = os.path.join(dir_to_search, filename)
        
        #return the image path
        return file_path
