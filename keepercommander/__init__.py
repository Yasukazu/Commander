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

import logging
from logging import handlers
import locale # for strxfrm sort
import pathlib
from pathlib import Path

__version__ = '4.19'
__revision__ = "2020-02-16"
__config_filename__ = 'config.json'
__logging_format__ = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"



locale.setlocale(locale.LC_ALL, '' if locale.getdefaultlocale() else 'ja_JP.UTF-8')

pager = None

from os import getenv
__user_id__ = getenv('KEEPER_USER_ID')
__pwd__ = getenv('KEEPER_PASSWORD')