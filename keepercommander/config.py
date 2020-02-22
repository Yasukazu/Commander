# config module

import logging
from logging import handlers
import locale # for strxfrm sort
import pathlib
from pathlib import Path
import json

__revision__ = "2020-02-222"
__config_filename__ = 'config.json'
__logging_format__ = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"


class Config(ABC):
    @abstractmethod
    @classmethod
    def set(cls, **kwargs):
        pass

    @abstractmethod
    @classmethod
    def start(cls):
        pass


class Logging(Config):
    level = logging.ERROR
    format = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"
    path = '.'
    filename = 'keeper.log'
    handler = None

    @classmethod
    def set(cls, **logging_dict): # force=True, path='.', filename='keeper.log', **kwargs):
        try:  # pick up keys from config.json file
            logging_keys = {'level', 'format', 'path', 'filename'}
            for key in logging_keys:
                value = logging_dict.get(key)
                if value:
                    level_set = {'DEBUG','INFO','WARNING','ERROR','CRITICAL'}
                    if key == 'level' and value not in level_set:
                        logging.warning(f"'level' must be in {level_set}")
                        continue
                    setattr(cls, key, value)
                        
        except Exception:
            logging.exception('Unknown exception happend.')
            raise
    
    @classmethod
    def start(cls):
        fullpath = Path(cls.path) / cls.filename
        cls.handler = handlers.RotatingFileHandler(fullpath, maxBytes=32768, backupCount=1)    
        logging.basicConfig(force=True, level=cls.level, format=cls.format, handlers=[cls.handler])
        logging.info(f"Logging.basicConfig is set: level={cls.level}, format={cls.format}, handler={cls.handler}.")




locale.setlocale(locale.LC_ALL, '' if locale.getdefaultlocale() else 'ja_JP.UTF-8')

pager = None

def set_by_json_file(config_filename=__config_filename__):
    pth = Path(config_filename)
    if pth.exists():
        try:  # pick up keys from config.json file
            with open(config_filename) as config_file:
                config_dict = json.load(config_file)
                config_class_key_set = {'logging':Logging}
                for k,cls in config_class_key_set:
                    if k in config_dict.keys():
                        cls.set(**config_dict[k])
        except json.JSONDecodeError as err:  # msg, doc, pos:
            emsg = f"Error: Unable to parse: {err.doc} ; at {err.pos} ; in JSON file: {self.config_filename}"
            logging.error(f"msg:{err.msg}, doc:{err.doc}, pos:{err.pos}. {emsg}")
            from .error import DecodeError
            raise DecodeError(emsg) from json.JSONDecodeError
        except OSError as e:
            msg = f"{e.strerror}: Error: Unable to access config file: {config_filename}"
            logging.error(msg)
            from .error import OSException
            raise OSException(msg) from OSError
        except Exception:
            logging.exception('Unknown exception happend.')
            raise

def start():
    config_class_set = {Logging}
    for cls in config_class_set:
        cls.start()
from abc import ABC, abstractmethod
