from .cli import command_info
from prompt_toolkit.completion import WordCompleter
from .commands import register_commands, register_enterprise_commands, aliases, commands, enterprise_commands

command_info_keys = [k.split('|')[0] for k in command_info.keys()]
command_Dict_parser = {k:v.get_parser() for (k,v) in commands.items()}
command_Dict_option_string = {} # type: Dict[str, str]


command_Dict_option_string_actions = {k:v._option_string_actions for (k,v) in command_Dict_parser.items()}
command_info_dict = vars(command_info)
command_info_keys_completer = WordCompleter(command_info_keys)

