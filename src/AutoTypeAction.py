from dataclasses import dataclass
from enum import Enum
import pyautogui

from ulauncher.api.shared.action.BaseAction import BaseAction


class AutoTypeInputType(Enum):
    TEXT = 0
    KEY_PRESS = 1


class KeyPress(Enum):
    TAB = "tab"
    ENTER = "enter"


@dataclass
class AutoTypeInputEntry:
    input_type: AutoTypeInputType
    input_to_type: str


class AutoTypeInput:
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
        return AutoTypeInput()

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
