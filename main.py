from dataclasses import dataclass
from pathlib import Path

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from src.AutoTypeAction import AutoTypeActionStandInBuilder
from src.KeepassXC import KeepassXC

ICON_FILE = (Path(__file__).parent / 'images/keepass_logo.png').__str__()


class KeepassXcExtension(Extension):
    def __init__(self):
        super().__init__()
        keepass_controller = KeepassXcInteractionController()
        self.subscribe(PreferencesEvent, PreferencesEventListener(keepass_controller))
        self.subscribe(ItemEnterEvent, ItemEnterEventListener(keepass_controller))
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())


class KeywordQueryEventListener(EventListener):
    def __init__(self, keepass_controller, preferences):
        super().__init__()
        self.keepass_controller: KeepassXcInteractionController = keepass_controller

    def on_event(self, event: KeywordQueryEvent, extension: KeepassXcExtension):
        query = event.get_query().get_argument(default="")

        return RenderResultListAction([
            ExtensionResultItem(
                name=entry,
                description="Open Keepass XC",
                icon=ICON_FILE,
                on_enter=ExtensionCustomAction({"entry": entry, "current_query": f"{event.get_keyword()} {query}"},
                                               keep_app_open=True),
                on_alt_enter=CopyToClipboardAction(entry)
            )
            for entry in self.keepass_controller.search(query)
        ][:int(extension.preferences['item_limit'])])


class ItemEnterEventListener(EventListener):
    def __init__(self, keepass_controller):
        self.keepass_controller: KeepassXcInteractionController = keepass_controller

    def on_event(self, event: ItemEnterEvent, extension: KeepassXcExtension):
        data = event.get_data()
        entry = data.get("entry", None)
        current_query = data.get("current_query", None)

        entry_info = self.keepass_controller.show(entry)

        items = []
        if entry_info.password:
            items.append(ExtensionResultItem(
                name=f"Password: {entry_info.password}",
                description="Autotype/Copy Password",
                icon=ICON_FILE,
                highlightable=False,
                on_enter=AutoTypeActionStandInBuilder().type(entry_info.password).build(),
                on_alt_enter=CopyToClipboardAction(entry_info.password)
            ))

        if entry_info.username:
            items.append(ExtensionResultItem(
                name=f"Username: {entry_info.username}",
                description="Autotype/Copy Username",
                icon=ICON_FILE,
                highlightable=False,
                on_enter=AutoTypeActionStandInBuilder().type(entry_info.username).build(),
                on_alt_enter=CopyToClipboardAction(entry_info.username),
            ))

        if entry_info.username and entry_info.password:
            items.append(ExtensionResultItem(
                name="Autotype credentials",
                description="Autotype Username and Password",
                icon=ICON_FILE,
                highlightable=False,
                on_enter=AutoTypeActionStandInBuilder().credentials(entry_info.username, entry_info.password).build(),
            ))

        if entry_info.url:
            items.append(ExtensionResultItem(
                name=f"Open Url",
                description=entry_info.url,
                icon=ICON_FILE,
                highlightable=False,
                on_enter=OpenUrlAction(entry_info.url),
                on_alt_enter=CopyToClipboardAction(entry_info.url),
            ))

        return RenderResultListAction(items)


class PreferencesEventListener(EventListener):
    def __init__(self, keepass_controller):
        super().__init__()
        self.__keepass_controller = keepass_controller

    def on_event(self, event: PreferencesEvent, extension: KeepassXcExtension):
        extension.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.__keepass_controller, event.preferences))


class PreferencesUpdateEventListener(EventListener):
    def __init__(self):
        super().__init__()
        self.id_update = "item_limit"

    def on_event(self, event: PreferencesUpdateEvent, extension: KeepassXcExtension):
        if event.id != self.id_update:
            pass

        extension.preferences[self.id_update] = event.new_value


@dataclass
class EntryInfo:
    title: str
    username: str
    password: str
    url: str
    notes: str
    uuid: str
    tags: str


class KeepassXcInteractionController:
    def __init__(self):
        self.__keepass = KeepassXC()
        self.prefixes = ["Title:", "UserName:", "Password:", "URL:", "Notes:", "Uuid:", "Tags:"]

    def search(self, query: str) -> [str]:
        query = query if query else "*"
        return self.__keepass.interact(f"search {query}")

    def show(self, entry: str) -> EntryInfo:
        output = self.__keepass.interact(f"show -s \"{entry}\"")

        properties = []
        prefix_pointer = 0
        current_property = None

        for line in output:
            if line.startswith(self.prefixes[prefix_pointer]):
                if current_property is not None:
                    properties.append(current_property)

                current_property = ""
                current_property += line[len(self.prefixes[prefix_pointer]):].strip()
                prefix_pointer += 1
            else:
                current_property += line.strip()
        properties.append(current_property)

        return EntryInfo(title=properties[0],
                         username=properties[1],
                         password=properties[2],
                         url=properties[3],
                         notes=properties[4],
                         uuid=properties[5],
                         tags=properties[6])

    def show_details(self, entry: str):
        output = self.__keepass.interact(f"show -a Title -a UserName -a Password \"{entry}\"")
        title = output[0]
        username = output[1]
        password = output[2]
        return title, username, password


if __name__ == '__main__':
    KeepassXcExtension().run()
