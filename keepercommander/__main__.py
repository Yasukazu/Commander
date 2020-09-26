# -*- coding: utf-8 -*-
#  _  __
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|
#
# Keeper Commander
# Copyright 2018 Keeper Security Inc.
# Contact: ops@keepersecurity.com
#


import re
import sys
import os
import argparse
from argparse import Namespace
import shlex
import base64
import json
from json import JSONDecodeError
import logging
from typing import List, Optional, Tuple, Dict
import locale
import configargparse
from .params import KeeperParams
from .error import InputError, OSException, ArgumentError, ConfigError
from . import cli
from . import config
from . import __version__
from . import CONFIG_FILENAME

logger = logging.getLogger(__name__)

# PARSER = argparse.ArgumentParser(prog='keeper', add_help=False)
PARSER = configargparse.ArgParser(prog='keeper', add_help=False)
PARSER.add_argument('--server', '-ks', dest='server', action='store', help='Keeper Host address.')
PARSER.add_argument('--user', '-ku', dest='user', action='store', help='Email address for the account.')
PARSER.add_argument('--password', '-kp', dest='password', action='store', help='Master password for the account.')
PARSER.add_argument('--version', dest='version', action='store_true', help='Display version')
PARSER.add_argument('--config', dest='config', action='store', help='Config file to use')
PARSER.add_argument('--debug', dest='debug', action='store_true', help='Turn on debug mode')
PARSER.add_argument('--batch-mode', dest='batch_mode', action='store_true', help='Run commander in batch or basic UI mode.')
PARSER.add_argument('--locale', dest='locale', action='store', help="Locale like 'en_US'")
PARSER.add_argument('command', nargs='?', type=str, action='store', help='Command') # default='shell', const='shell', : default=shell')
PARSER.add_argument('options', nargs='*', action='store', help='Options')


pager = None


def usage(m):
    # print(m)
    # parser.print_help()
    # cli.display_command_help(show_enterprise=True, show_shell=True)
    raise ArgumentError(m + ':' + PARSER.format_help()) # sys.exit(1)


PARSER.error = usage


def handle_exceptions(exc_type, exc_value, exc_traceback):
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    input('Press Enter to exit')


def main(argv: List[str] = None, config_only: bool = False, from_package=False) -> Optional[Tuple[KeeperParams, Namespace, List[str]]]:
    if from_package:
        sys.excepthook = handle_exceptions
    if argv is None:
        argv = sys.argv
    argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', argv[0])
    try:
        opts, flags = PARSER.parse_known_args(argv[1:])
        # o_locale = locale.setlocale(locale.LC_ALL, opts.locale) if opts.locale else None
        config_file = opts.config or CONFIG_FILENAME
        params = KeeperParams()
        params.set_params_from_config_file(config_file) or {}
        config_from_argv = {k: v for k, v in vars(opts).items() if v}
        params.set_params_from_config_dict(config_from_argv)
        # config_objs = config.set_by_json_file(config_file)
        # if file_base_config: config.start(file_base_config)
    except ConfigError as e:
        logger.exception("Config file error.")
        print(e)
        raise
    except ArgumentError as e:
        logger.error("Command line parameter error!")
        print(e)
        raise  # sys.exit(1)
    except locale.Error as e:
        logger.error(e, f" is an unavailable locale.")
        raise  # params = KeeperParams()

    # merge opts to file_base_config

    # params = KeeperParams(config={'locale': olocale})

    '''
    if opts.config:
        try:
            params.set_params_from_config(opts.config)
        except InputError as e:
            logger.error('Config file is not proper format: ' + e.message)
            raise
        except OSException as e:
            logger.error('Config file is not accessible: ' + e.message)
            raise
    logging.basicConfig(
        level=logging.WARNING if params.batch_mode else logging.INFO,
        format=__logging_format__)
    '''
    if opts.debug:
        params.debug = opts.debug

    if opts.batch_mode:
        params.batch_mode = True

    if opts.server:
        params.server = 'https://{0}/api/v2/'.format(opts.server)

    if opts.user:
        params.user = opts.user

    if opts.password:
        params.password = opts.password
    else:
        from . import __pwd__
        # pwd = os.getenv('KEEPER_PASSWORD')
        if __pwd__:
            params.password = __pwd__

    if config_only:
        return params, opts, flags
    
    if opts.version:
        print('Keeper YCommander, version {0}'.format(__version__))
        return

    if flags and len(flags) > 0:
        if flags[0] == '-h':
            flags.clear()
            opts.command = '?'

    if (opts.command or '') in {'?', ''}:
        if opts.command == '?' or not params.commands:
            usage('')

    if params.timedelay >= 1 and params.commands:
        cli.runcommands(params)
    else:
        if opts.command != 'shell':
            if opts.command:
                flags = ' '.join([shlex.quote(x) for x in flags]) if flags is not None else ''
                options = ' '.join([shlex.quote(x) for x in opts.options]) if opts.options is not None else ''
                command = ' '.join([opts.command, flags, options])
                params.commands.append(command)
            params.commands.append('q')
        cli.loop(params)


if __name__ == '__main__':
    main()
