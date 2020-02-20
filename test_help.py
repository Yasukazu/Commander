from keepercommander.help import command_info_keys_completer
from prompt_toolkit import prompt
if __name__ == "__main__":
    text = prompt('>', completer=command_info_keys_completer)
    print(text)