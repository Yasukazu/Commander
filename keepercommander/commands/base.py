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

import argparse
import shlex
import logging
import os
import re
import csv
import sys

from tabulate import tabulate
from ..params import KeeperParams
from ..subfolder import try_resolve_path
from ..error import ArgumentError,ParseError, SequenceError, ResolveError
from ..pager import TablePager
from .. import api

aliases = {}        # type: {str, str}
commands = {}       # type: {str, Command}
enterprise_commands = {}     # type: {str, Command}

def register_commands(commands, aliases, command_info):
    from .record import register_commands as record_commands, register_command_info as record_command_info
    record_commands(commands)
    record_command_info(aliases, command_info)

    from .folder import register_commands as folder_commands, register_command_info as folder_command_info
    folder_commands(commands)
    folder_command_info(aliases, command_info)

    from .register import register_commands as register_commands, register_command_info as register_command_info
    register_commands(commands)
    register_command_info(aliases, command_info)

    from .utils import register_commands as misc_commands, register_command_info as misc_command_info
    misc_commands(commands)
    misc_command_info(aliases, command_info)

    from .. import importer
    importer.register_commands(commands)
    importer.register_command_info(aliases, command_info)

    from .. import plugins
    plugins.register_commands(commands)
    plugins.register_command_info(aliases, command_info)


def register_enterprise_commands(commands, aliases, command_info):
    from .enterprise import register_commands as enterprise_commands, register_command_info as enterprise_command_info
    enterprise_commands(commands)
    enterprise_command_info(aliases, command_info)


def user_choice(question, choice, default='', show_choice=True, multi_choice=False):
    choices = [ch.lower() if ch.upper() == default.upper() else ch.lower() for ch in choice]

    result = ''
    while True:
        pr = question
        if show_choice:
            pr = pr + ' [' + '/'.join(choices) + ']'

        pr = pr + ': '
        result = input(pr)

        if len(result) == 0:
            return default

        if multi_choice:
            s1 = set([x.lower() for x in choices])
            s2 = set([x.lower() for x in result])
            if s2 < s1:
                return ''.join(s2)
            pass
        elif any(map(lambda x: x.upper() == result.upper(), choices)):
            return result

        logging.error('Error: invalid input')



def raise_parse_exception(m):
    '''Raise parse exception in Command'''
    raise ParseError(m)

def suppress_exit():
    logging.info("Supress Exit.")


def dump_report_data(data, headers, title=None, is_csv = False, filename=None, append=False):
    # type: (list, list, str, bool, str, bool) -> None
    if is_csv:
        if filename:
            _, ext = os.path.splitext(filename)
            if not ext:
                filename += '.csv'
        fd = open(filename, 'a' if append else 'w') if filename else sys.stdout
        csv_writer = csv.writer(fd)
        if title:
            csv_writer.writerow([])
            csv_writer.writerow([title])
            csv_writer.writerow([])
        elif append:
            csv_writer.writerow([])
        if headers:
            csv_writer.writerow(headers)
        for row in data:
            csv_writer.writerow(row)
        if filename:
            fd.flush()
            fd.close()
    else:
        if title:
            print('\n{0}\n'.format(title))
        elif append:
            print('\n')
        print(tabulate(data, headers=headers))


parameter_pattern = re.compile(r'\${(\w+)}')

from abc import ABCMeta,abstractmethod

class Command(metaclass=ABCMeta):
    """Parent Command class"""
    PARSER = None
    
    @classmethod
    def parser(cls):
        return cls.PARSER

    @classmethod
    def parser_error(cls):
        '''Raise parse exception'''
        raise ParseException(f"Parse error in {cls.__name__}.")
    
    def get_parser(self):
        return self.__class__.PARSER
    
    @abstractmethod
    def execute(self, params:KeeperParams, **kwargs):# -> List[Record] or None:     # type: (KeeperParams, **any) -> any
        raise NotImplementedError()

    def execute_args(self, params:KeeperParams, args:str, **kwargs):
        # type: (Command, KeeperParams, str, dict) -> any

        global parameter_pattern
        try:
            parser = self.get_parser()
            d = {}
            d.update(kwargs)
            if parser is not None:
                if args:
                    pos = 0
                    value = args
                    while True:
                        m = parameter_pattern.search(value, pos)
                        if not m:
                            break
                        p = m.group(1)
                        if p in params.environment_variables:
                            pv = params.environment_variables[p]
                            value = value[:m.start()] + pv + value[m.end():]
                            pos = m.start() + len(pv)
                        else:
                            pos = m.end() + 1
                    args = value
                shlex_split = shlex.split(args)
                opts = parser.parse_args(shlex_split)
                d.update(opts.__dict__)
            return self.execute(params, **d)
        except ValueError as ve:
            logging.exception(f"{ve} : not a proper value.")
        except Exception:
            logging.exception("Unhandled exception occured.")

    #def get_parser(self):   # type: () -> argparse.ArgumentParser or None        return None

    def is_authorised(self):
        return True

    @classmethod
    def resolve_uid(cls, name: str, params: KeeperParams, **kwargs) -> str :
        '''Resolve uid from name or record_cache
            Raise ResolveError if not proper number
        '''
        if not len(name):
            raise ArgumentError("Parameter string length must be larger than 0")
        if name in params.record_cache:
            return name
        else:
            folder, name = try_resolve_path(params, name)
            folder_uid = folder.uid or ''
            if folder_uid in params.subfolder_record_cache:
                for uid in params.subfolder_record_cache[folder_uid]:
                    r = api.get_record(params, uid)
                    if r.title.lower() == name.lower():
                        return uid
            else:
                raise ResolveError("No UID is resolved!")
    
    @classmethod
    def get_uid(cls, uid: str) -> str:
        ''' Resolve uid by line number of previous list command
            Raise SequenceError or ArgumentError if not proper number
        '''
        if not TablePager.table:
            raise SequenceError("Record number specify needs to be after pager or web showed records.")
        if not uid or len(uid) == 0:
            raise ArgumentError("Not proper string is given!")
        import re
        mt = re.fullmatch(r"(\d+)", uid)
        if not mt:
            raise ArgumentError(f"{uid} is not a proper string for an integer value!")
        num = int(mt.group(0))
        lines = TablePager.table
        if num <= 0 or num > len(lines):
            raise ArgumentError(f"Specify (0 < number <= ({len(lines)}).")
        return lines[num - 1][1]
