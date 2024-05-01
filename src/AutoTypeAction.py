from dataclasses import dataclass
from enum import Enum
import pyautogui

from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction


class AutoTypeInputType(Enum):
    TEXT = "type --delay 100"
    KEY_PRESS = "key"


# class KeyPress(Enum):
#     TAB = "tab"
#     ENTER = "enter"

class KeyPress(Enum):
    TAB = "Tab"
    ENTER = "Return"


@dataclass
class AutoTypeInputEntry:
    input_type: AutoTypeInputType
    input_to_type: str


class AutoTypeActionBuilder:
    def __init__(self):
        self.__inputs: [AutoTypeInputEntry] = []

    def key_press(self, key: KeyPress):
        self.__inputs.append(AutoTypeInputEntry(input_type=AutoTypeInputType.KEY_PRESS, input_to_type=key.value))
        return self

    def text(self, text: str):
        self.__inputs.append(AutoTypeInputEntry(input_type=AutoTypeInputType.TEXT, input_to_type=text))
        return self

    def credentials(self, username: str, password: str):
        self.text(username)
        self.key_press(KeyPress.TAB)
        self.text(password)
        self.key_press(KeyPress.ENTER)
        return self

    def build(self):
        return AutoTypeAction(self.__inputs)


class AutoTypeAction(BaseAction):
    """
    Autotype text

    :param [AutoTypeInputEntry] auto_type_input: input to autotype
    """
    @staticmethod
    def builder():
        return AutoTypeActionBuilder()

    def __init__(self, auto_type_input):
        self.auto_type_input = auto_type_input

    def keep_app_open(self):
        return False

    def run(self):
        for entry in self.auto_type_input:
            if entry.input_type == AutoTypeInputType.KEY_PRESS:
                pyautogui.press(entry.input_to_type)
                continue

            pyautogui.typewrite(entry.input_to_type)


class AutoTypeActionStandInBuilder:
    def __init__(self):
        self.bin = "xdotool"
        self.window_minimize = "getactivewindow windowminimize --sync"
        self.commands: [AutoTypeInputEntry] = []

    def type(self, text: str):
        self.commands.append(AutoTypeInputEntry(input_type=AutoTypeInputType.TEXT, input_to_type=text))
        return self

    def key_press(self, key: KeyPress):
        self.commands.append(AutoTypeInputEntry(input_type=AutoTypeInputType.KEY_PRESS, input_to_type=key.value))
        return self

    def credentials(self, username: str, password: str):
        self.type(username)
        self.key_press(KeyPress.TAB)
        self.type(password)
        self.key_press(KeyPress.ENTER)
        return self

    def build(self):
        built_commands = [f"{self.bin} {self.window_minimize if index == 1000000 else ''} {entry.input_type.value} {entry.input_to_type}"
                          for index, entry in enumerate(self.commands)]
        command = " && ".join(built_commands)
        return RunScriptAction(command)
