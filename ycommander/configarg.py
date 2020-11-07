# -*- coding: utf-8 -*-

import re
import sys
from argparse import Namespace
import logging
from typing import List, Optional, Tuple, Dict
import locale
from pathlib import Path

import configargparse

from .params import KeeperParams
from .error import InputError, OSException, ArgumentError, ConfigError
from . import CONFIG_FILENAME, __config_fullpath

logger = logging.getLogger(__name__)

# PARSER.add_argument('--server', '-ks', dest='server', action='store', help='Keeper Host address.')
# PARSER.add_argument('--version', dest='version', action='store_true', help='Display version')
PARSER = configargparse.ArgParser(default_config_files=[__config_fullpath])  # ArgumentParser(prog='keeper', add_help=False)
PARSER.add_argument('--config', '-cg', dest='config', action='store', help='Config file to use')
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


def configure(argv: List[str] = None, from_package=False) -> Optional[Tuple[KeeperParams, Namespace, List[str]]]:
    if from_package:
        sys.excepthook = handle_exceptions
    if argv is None:
        argv = sys.argv
    argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', argv[0])
    try:
        opts, flags = PARSER.parse_known_args(argv[1:])
        params = KeeperParams()
        config_file = opts.config or CONFIG_FILENAME
        if Path(config_file).exists():
            params.set_params_from_config_file(config_file)
        valid_opts = {k: v for k, v in vars(opts).items() if v}
        params.set_params_from_config_dict(valid_opts)
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

    return params, opts, flags
