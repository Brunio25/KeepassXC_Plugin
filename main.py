from dataclasses import dataclass

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.utils.fuzzy_search import get_score
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem

from src.AutoTypeAction import AutoTypeAction
from src.KeepassXC import KeepassXC


class KeepassXcExtension(Extension):
    def __init__(self):
        super().__init__()
        keepass_controller = KeepassXcInteractionController()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(keepass_controller))
        self.subscribe(ItemEnterEvent, ItemEnterEventListener(keepass_controller))


class KeywordQueryEventListener(EventListener):
    def __init__(self, keepass_controller):
        super().__init__()
        self.keepass_controller: KeepassXcInteractionController = keepass_controller

    def on_event(self, event: KeywordQueryEvent, extension: KeepassXcExtension):
        query = event.get_query().get_argument(default="")

        return RenderResultListAction([
            ExtensionSmallResultItem(
                name=entry,
                description="Open Keepass XC",
                icon="/home/ctw03249/.local/share/ulauncher/extensions/KeepassXC_Plugin/images/keepass_logo.png",
                on_enter=ExtensionCustomAction({"entry": entry, "current_query": f"{event.get_keyword()} {query}"},
                                               keep_app_open=True),
            )
            for entry in self.keepass_controller.search(query)
        ])


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
                description="Copy/Autotype Password",
                on_enter=CopyToClipboardAction(entry_info.password),
                # on_enter=AutoTypeAction.builder().text(entry_info.password).build(),
            ))

        if entry_info.username:
            items.append(ExtensionResultItem(
                name=f"Username: {entry_info.username}",
                description="Copy/Autotype Username",
                on_enter=CopyToClipboardAction(entry_info.username),
                # on_enter=AutoTypeAction.builder().text(entry_info.username).build(),
            ))

        # if entry_info.username and entry_info.password:
        #     items.append(ExtensionResultItem(
        #         name="Autotype credentials",
        #         description="Autotype Username and Password",
        #         on_enter=AutoTypeAction.builder().credentials(entry_info.username, entry_info.password).build(),
        #     ))

        if entry_info.url:
            items.append(ExtensionResultItem(
                name=f"Open Url",
                description=entry_info.url,
                on_enter=OpenUrlAction(entry_info.url),
                on_alt_enter=CopyToClipboardAction(entry_info.url),
            ))

        return RenderResultListAction(items)


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
