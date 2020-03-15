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

__version__ = '4.19'
__revision__ = "2020-03-15"
__config_filename__ = 'config.json'
__logging_format__ = "%(levelname)s: %(message)s by %(module)s.%(funcName)s in %(fileName)s:%(lineno) at %(asctime)s"
__default_locale__ = 'en_US'



__user_id__ = getenv('KEEPER_USER_ID')
__pwd__ = getenv('KEEPER_PASSWORD')