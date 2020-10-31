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

import locale  # for strxfrm sort
from os import getenv
import sys, os

__version__ = '4.19'
__revision__ = "2020-04-26"
__logging_format__ = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"
__default_locale__ = 'en_US'

__user_id__ = getenv('KEEPER_USER_ID')
__pwd__ = getenv('KEEPER_PASSWORD')

CONFIG_FILENAME = getenv('KEEPER_CONFIG') or 'keeper.conf'
CONFIG_PATH = getenv('KEEPER_CONFIG_PATH') or '.'
from pathlib import Path
__config_fullpath = Path(CONFIG_PATH) / CONFIG_FILENAME
import configargparse
PARSER = configargparse.ArgParser(default_config_files=[__config_fullpath])  # ArgumentParser(prog='keeper', add_help=False)
PARSER.add('--user', '-ku', dest='user', action='store', env_var='KEEPER_USER', help='Email address for the account.')
PARSER.add('--password', '-kp', dest='password', action='store', env_var='KEEPER_PASSWORD', help='Master password for the account.')

import logging
import pylogrus
logging.setLoggerClass(pylogrus.PyLogrus)