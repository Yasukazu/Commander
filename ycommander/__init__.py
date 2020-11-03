# -*- coding: utf-8 -*-
#  _  __
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|
#
# Keeper Commander
# Copyright 2019 Keeper Security Inc.
# Contact: ops@keepersecurity.com
#

from os import getenv

__version__ = '4.19'
__revision__ = "2020-04-26"
__logging_format__ = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"
__default_locale__ = 'en_US'

__user_id__ = getenv('KEEPER_USER_ID')
__pwd__ = getenv('KEEPER_PASSWORD')

from ycommander import PARSER
from ycommander.configarg import PARSER

CONFIG_FILENAME = getenv('KEEPER_CONFIG') or 'keeper.conf'
CONFIG_PATH = getenv('KEEPER_CONFIG_PATH') or '.'
from pathlib import Path
__config_fullpath = Path(CONFIG_PATH) / CONFIG_FILENAME

import logging
import pylogrus
logging.setLoggerClass(pylogrus.PyLogrus)