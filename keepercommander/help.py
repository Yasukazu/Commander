from .cli import command_info
from prompt_toolkit.completion import NestedCompleter
from .commands import register_commands, register_enterprise_commands, aliases, commands, enterprise_commands
from collections import deque
command_info_keys = [k.split('|')[0] for k in command_info.keys()]
command_Dict_parser = {k:v.get_parser() for (k,v) in commands.items()}
command_Dict_option_string = {} # type: Dict[str, set]
for cmd, psr in command_Dict_parser.items():
    try:
        command_Dict_option_string[cmd] = {k for k in psr._option_string_actions if k.startswith('--')}
    except:
        pass

command_info_keys_completer = NestedCompleter.from_nested_dict(
    command_Dict_option_string
)
print()
# = WordCompleter(command_info_keys)

