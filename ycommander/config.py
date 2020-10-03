# config module\\\\\\# for strxfrm sort
import pathlib
from pathlib import Path
import json
from abc import ABC, abstractmethod
import locale
from .error import ConfigError
import logging
from typing import Dict
from typing import Set

logger = logging.getLogger(__name__)
config_filename = 'keeper-config.json'
__logging_format__ = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"


class Config(ABC):
    @abstractmethod
    def start(self):
        pass


class Logging(Config):
    level = logging.INFO
    format = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno)d at %(asctime)s"
    #path = '.'
    #filename = 'keeper.log'

    def __init__(self, **logging_dict):
        '''Set logging.'level', 'format', 'path', 'filename'
        '''
        sets = {}
        logging_keys = {'level', 'format', 'path', 'filename'}
        for key in logging_keys:
            value = logging_dict.get(key)
            if value:
                level_set = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
                if key == 'level' and value not in level_set:
                    raise ConfigError(f"'level' must be in {level_set}")
                sets[key] = value
        self.config = sets

    def start(self):
        '''basicConfig starts 
        '''
        # fullpath = Path(cls.path) / cls.filename
        # rfHandler = handlers.RotatingFileHandler(fullpath, maxBytes=32768, backupCount=1)
        # cls.formatter = logging.Formatter(cls.format)
        # rfHandler.setFormatter(cls.formatter)
        logging.basicConfig(**self.config)  # handlers=[logging.StreamHandler()], 
        # logging.info(f"Logging.basicConfig is set: level={cls.level}, format={cls.formatter.format}, handlers={cls.handlers}.")
        # return cls.handlers


class Locale(Config):
    LC = 'en_US'
    ENCODING = 'utf8'

    def __init__(self, code: str):
        self.lc, self.encoding = locale.getlocale()
        self.default_lc, self.codepage = locale.getdefaultlocale()
        if code:
            self.lc = code.split('.')[0]
        """
        if lc in locale.locale_aliases().keys():
            self.lc = lc
        else:
            raise ConfigError("{lc} is not in the alias list.")
        """

    def start(self):
        pass  # locale.setlocale(locale.LC_ALL, '.'.join([self.lc, Locale.ENCODING]))


pager = None

key_Dict_config_class = {'logging': Logging, 'locale': Locale}


def set_by_json_file(config_filename=config_filename):
    pth = Path(config_filename)
    if pth.exists():
        try:  # pick up keys from config.json file
            with open(config_filename) as config_file:
                config_dict = json.load(config_file)
                config_sets = {}
                for k, cls in key_Dict_config_class.items():
                    if k in config_dict.keys():
                        config_sets[k] = cls(config_dict[k])
                return config_sets
        except json.JSONDecodeError as err:  # msg, doc, pos:
            emsg = f"Error: Unable to parse: {err.doc} ; at {err.pos} ; in JSON file: {config_filename}"
            logging.error(f"msg:{err.msg}, doc:{err.doc}, pos:{err.pos}. {emsg}")
            from .error import DecodeError
            raise ConfigError(emsg) from json.JSONDecodeError
        except OSError as e:
            msg = f"{e.strerror}: Error: Unable to access config file: {config_filename}"
            logging.error(msg)
            from .error import OSException
            raise ConfigError(msg) from OSError
        except Exception:
            logging.exception('Unknown exception happend.')
            raise


def start(config_set: Dict[str, Config]):
    for name, obj in config_set.items():
        obj.start()