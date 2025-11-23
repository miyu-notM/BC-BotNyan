import os
import asyncio
import socketio
import json
import logging
import logging.config
import time
import random
from collections import defaultdict

from colorama import Fore
from lzstring import LZString

"""
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s:%(message)s'+Fore.RESET, 
    level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
BOT.LOG_CONFIG_SET = 1
"""

# TODO: 没有良好的检测被踢出的办法，目前使用的是定期重启
# TODO: 更改为配置文件形式


class BOT:
    def __init__(
        self,
        username,
        password,
        chatroom={"Name": "bot test", "Description": "nya!", "Space": "X"},
        logger=None,
    ):
        self.sio = socketio.AsyncClient(reconnection=False, logger=False)

        if not logger:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        """
        self.logger = logging.getLogger(str(id(self))) # so its unique... right?

        log_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d %(levelname)s:%(message)s'+Fore.RESET,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(log_formatter)
        self.logger.addHandler(stream_handler)
        
        if log_file:
            file_logger = logging.FileHandler(log_file)
            file_logger.setLevel(logging.DEBUG)
            file_logger.setFormatter(log_formatter)
            self.logger.addHandler(file_logger)

        self.logger.debug("test")

        logging.getLogger('socketio').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)
        """

        self.player = {}
        self.others = defaultdict(dict)
        self.inChatRoom = ""
        self.chatrooms = None
        self.appearance = json.loads(
            LZString.decompressFromBase64(
                "NobwRAcghgtgpmAXGAEgBgJwFY1gDRgDiATgPYCuADkqnAJYDmAFgC75gDCpANqcTQBE4AMyjlubAL55w0eDQDKMKN27sSFasgBCpACYBPAKqVKcfgS69+yAOpM6LBAQAKZM8RYGk4ACoGzJAA7cW5JaVlYBGQlFTUCDSoaXUMAGVIAd3N2Kz5BETEJMAjIKJoUKDpiADEyIJYMdTIk5Aqq2tJ6nJ485ABiPUGh4plS+VbK4m0oAGMAawBGACMmzXLJ6fnu6xoBocGRyPGwAFEDOCWyDIBnBdWW0/PLzOvt3rAhUXEpUblox7gt3uWgBr0sPRsHwK30OY3+Z0BdwSzRBCOuACY3pDPoUfkd/gI6NcZsQ4HA2Mi1sgALIUFhMLH5L5FEp/GgQOimbiI4HszmUblgzgQpm42Fs5AucjXa4GVKMVhIogomhSmXecE7ZA4mGssoxJhwFDZSkPNydChBIW5bHQlm/fVQ5kU5VU2hQPSM7V2vFw5LcaUM00g7QB65B4Vap1ivXHE4wUgsOgzTq85DxxPJ1Oa946+340Uw4PrIJ6a0i73O8WOgDSjicQROUGIGLTqEmAEEZjNAdc+AZMTmbMAwH0BOOwABdWP/OssBu+SrcBQsYhQShKxIgxd0Zer9flqN530SsAKGbN4Rtji8eldnsy/tekd9bQLN9vqeudzmLw+MD+IEiAhKo4QOscEDkC2cBGEEdDCHwMDXreEY2oW+Z+jovDSnAm4qjE5COF60a6uB/wrqQ8x0EEDCtsWBGOOkWQWJGuY+tWxwAEp0EsSydEKW7JGuxHHuw5oeH+iB+AE0QgWEM40NSlR6C4UD1HQPL0WAqnqYCInsQpOhqXoHZBHM3IuoJyDccwLCmeZ5LPqO1QAMwLG5LlToZtBwNwQJaQoTCkHpQ5IC+CxYO57leWR7JQdccAcOubYVC6aGVjGsXIIQzZOFMvksIOroPDlnjmIebFVt5hB0GpLC6BkeFum0xD3r2/aeaFGWkQW2XcFAMqAgALG2hD9YNFWQn0LloDNM0cf83G8fxI1aS1bWPsQBhKulJEYaeY2kAAbppxUgodJ2TWFo4CGgt23TFvVgNUAZ0GWbYvYR71dXtJ6Oi45LaHAnpaQAkk4MBCEdyYhaxw6/ewokEKJk7fqQEneFJAEycEoThJOQA"
            )
        )
        self.last_keepalive = 0
        self.is_logged_in = False
        self.current_chatroom = {}
        self.send_event_queue = asyncio.Queue()
        self.received_event_queue = asyncio.Queue()
        self.account = (username, password)
        self.chatroom = chatroom
        self.last_received = 0

        # self.sender = asyncio.create_task(self.sio_event_sender())
        # self.event_handler = None
        # self.register_handlers()  # 注册event响应事件

        self.background_tasks = dict.fromkeys(["sender","event_handler","keep_alive"])
        self.background_tasks['sender'] = asyncio.create_task(self.sio_event_sender())
        self.background_tasks['event_handler'] = self.register_handlers()
        # self.sio.start_background_task(self.sio_event_sender) # 开始发送event
        

    @staticmethod
    def exit_with_error(status, wait=3):
        time.sleep(wait)
        os._exit(status)

    @staticmethod
    def decode_compressed_list(something):
        if isinstance(something, str):  # compressed base64ed LZ-Compressed string
            try:
                res = json.loads(LZString.decompressFromUTF16(something))  # type: ignore
            except:
                res = {}
        elif isinstance(something, dict) or isinstance(
            something, set
        ):  # data is already decompressed
            res = something
        else:
            logging.error(f"unrecognized data type: {type(something)}")
            raise AssertionError
        return res

    @staticmethod
    async def CharacterMinify(C, l):
        return {k: v for k, v in C.items() if k in l}

    @staticmethod
    def dict_update_existing(d1, d2):
        # update d1 by d2, but only for existing keys in d1
        for k in d1.keys() & d2.keys():
            d1[k] = d2[k]

    # 后台运行的函数，自动发送simple_queue中的请求包
    async def sio_event_sender(self):
        while True:
            try:
                event, data = await self.send_event_queue.get()
                await self.sio.emit(event, data)
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                self.logger.debug("event sender is cancelled.")
                return

    async def server_send(self, event, data=None, now=False):
        # self.logger.info(f"sending data {event} {str(data)[:20]}")
        if now:
            await self.sio.emit(event, data)
        else:
            self.send_event_queue.put_nowait((event, data))

    async def account_update(self, data):
        # self.logger.debug("updating account data to avoid being kicked out")
        await self.server_send("AccountUpdate", data)

    async def reset_appearance(self):
        data = {
            "AssetFamily": "Female3DCG",
            "Appearance": self.appearance,
            "ItemPermission": 1,
        }
        await self.server_send("AccountUpdate", data)

    async def update_appearance(
        self, member_id, appearance, pose=[], event=None, **kwargs
    ):
        C = None
        # if member_id is MemberNumber
        member_id = self.find_character(member_id)
        C = self.others.get(member_id, None)
        # else we assume it is OnlineID
        assert C
        data = {"ID": C["ID"], "ActivePose": pose, "Appearance": appearance}
        data.update(kwargs)
        # self.logger.debug(f"updating appearance {data}")
        event = event if event else "ChatRoomCharacterUpdate"
        C["Appearance"] = appearance
        await self.server_send(event, data)
        return True

    async def find_friends(self):
        await self.server_send("AccountQuery", {"Query": "OnlineFriends"})

    async def add_or_remove_friend(self, member_id, add=True):
        if add:
            if member_id not in self.player["FriendList"]:
                self.player["FriendList"].append(member_id)
        else:
            if member_id in self.player["FriendList"]:
                self.player["FriendList"].remove(member_id)
        await self.ServerPlayerRelationsSync(self.player)

    async def become_owner(self, member_id):
        # check ownership property instead
        # server_send("AccountOwnership",{"MemberNumber":member_id})
        owner = self.others.get(member_id, {}).get("Ownership")
        if owner and owner.get("MemberNumber", 0) != self.player["MemberNumber"]:
            return  # this member already has a owner

        await self.server_send(
            "AccountOwnership", {"MemberNumber": member_id, "Action": "Propose"}
        )

    async def become_lover(self, member_id):
        lovers = [num for num in self.others.get(member_id, {}).get("Lovership")]
        if lovers and self.player["MemberNumber"] in lovers:
            return  # bot is already lover

        await self.server_send(
            "AccountLovership", {"MemberNumber": member_id, "Action": "Propose"}
        )

    async def add_or_remove_submissive(self, member_id, add=True):
        if add:
            if member_id not in self.player["SubmissivesList"]:
                self.player["SubmissivesList"].add(member_id)
                await self.ServerPlayerRelationsSync(self.player)
        else:
            if member_id in self.player["SubmissivesList"]:
                self.player["SubmissivesList"].remove(member_id)
                await self.ServerPlayerRelationsSync(self.player)
            await self.server_send(
                "AccountOwnership", {"MemberNumber": member_id, "Action": "Release"}
            )

    async def create_chatroom(self, name, **kwargs):
        data = {
            "Name": "123456789",
            "Language": "CN",
            "Description": "bot test",
            "Background": "Introduction",
            "Private": False,
            "Locked": False,
            "Space": "",
            "Game": "",
            "Admin": [self.player["MemberNumber"]],
            "Ban": [],
            "Limit": 20,
            "BlockCategory": ["Leashing"],
            "MapData": {"Type": "Never"},
        }
        data.update(kwargs)
        data["Name"] = name
        self.logger.info(f"creating chatroom {data['Name']}.")
        self.logger.debug(f"creating chatroom. data is {data}")
        await self.server_send("ChatRoomCreate", data)

    async def update_description(self, des):
        self.logger.debug(f"updating player description to {des}")
        await self.server_send("AccountUpdate", {"Description": des})

    async def search_chatroom(self, name, **kwargs):
        data = {
            "Query": name.upper(),
            "Language": "",
            "Space": "",
            "Game": "",
            "FullRooms": True,
            "ShowLocked": True,
        }
        for k in data.keys() & kwargs.keys():  # 删掉['Name']
            data[k] = kwargs[k]
        await self.server_send("ChatRoomSearch", data)

    async def query_chatroom(self):
        self.chatrooms = None
        await self.search_chatroom("")

    def update_chatroom(self, data):
        self.chatrooms = data
        for chatroom in self.chatrooms:
            self.logger.debug(f"found chatroom {chatroom['Name']}")

    async def join_chatroom(self, name):
        data = {"Name": name}
        self.logger.info(f"joining chatroom. data: {data}")
        await self.server_send("ChatRoomJoin", data)

    async def join_or_create_chatroom(self, name, **kwargs):
        self.chatrooms = None
        await self.search_chatroom(name, **kwargs)
        while self.chatrooms == None:
            await asyncio.sleep(0.5)  # not an elegant way, would fix it

        if self.chatrooms:
            self.logger.debug("room already exist, joining")
            await self.join_chatroom(name)
        else:
            self.logger.debug("room not exist, creating")
            await self.create_chatroom(name, **kwargs)

    def is_arm_restrainted(self, member_id):
        Character = self.others.get(member_id)
        if not Character:
            self.logger.warning(f"Cannot check restraints on Character {member_id}")
            return
        for a in Character["Appearance"]:
            if a["Group"] == "ItemArms":
                return True
        return False

    def has_enough_permission(self, Character):
        # print(Character)
        permission = Character.get("ItemPermission")
        self.logger.info(
            f"Character {Character.get('MemberNumber')} permission is set to {permission}"
        )
        if not permission:
            return True
        if (
            (
                permission == 5
                and Character.get("Ownership", {}).get("MemberNumber", 0)
                != self.player["MemberNumber"]
            )  # permission is Owner Only but bot is not character's owner
            or (
                permission == 4
                and self.player["MemberNumber"]
                not in [
                    i.get("MemberNumber", 0) for i in Character.get("Lovership", [])
                ]
            )  # permission is Owner & Lover Only but bot is not character's owner or lover
            or (
                permission == 3
                and self.player["MemberNumber"] not in Character.get("WhiteList", [])
            )  # bot is not in white list
        ):
            return False
        return True

    def find_character(self, whatever):
        # cannot handle people with same name!
        if self.others.get(whatever):
            return whatever
        if isinstance(whatever, dict):
            return whatever.get("MemberNumber")
        if isinstance(whatever, str) and whatever.isdigit():
            whatever = int(whatever)
            if self.others.get(whatever):
                # this is a member id
                return whatever
        assert isinstance(whatever, str)
        for _, c in self.others.items():
            # use casefold() instead of lower() or upper() because some use names are in Latin or other language that lower() may return false answer
            # https://stackoverflow.com/a/29247821
            if (
                c.get("ID") == whatever
                or c.get("Name", "").casefold() == whatever.casefold()
                or c.get("Nickname", "").casefold() == whatever.casefold()
            ):
                return c["MemberNumber"]
        return None

    async def keep_alive(self):
        self.logger.info("started keep alive background task")
        self.last_keepalive = time.time()
        while True:
            if time.time() - self.last_keepalive > 300:
                self.last_keepalive = time.time()
                await self.do_keep_alive()
                self.logger.debug(f"last receive event time: {self.last_received}, now: {time.time()}")
            else:
                await asyncio.sleep(60)

            # 踢出检测：如果在30分钟内没有收到服务器的任何消息，就是被踢出了
            if (now := time.time()) - self.last_received >= 900:
                self.logger.error("疑似掉线，正在退出")
                # self.last_received = now  # 防止再次发送
                await self.disconnect()

    # don't use this function inside the main loop. use keep_alive() to call with an interval
    async def do_keep_alive(self):
        if not self.sio.connected:
            return
        choice = random.randint(0, 2)
        match choice:
            case 0:  # send something to the chat
                await self.server_send(
                    "ChatRoomChat",
                    {
                        "Content": "ChatSelf-ItemEars-Wiggle",
                        "Type": "Activity",
                        "Dictionary": [
                            {
                                "Tag": "SourceCharacter",
                                "Text": self.player["Nickname"],
                                "MemberNumber": self.player["MemberNumber"],
                            },
                            {
                                "Tag": "TargetCharacter",
                                "Text": self.player["Nickname"],
                                "MemberNumber": self.player["MemberNumber"],
                            },
                            {"FocusGroupName": "ItemEars"},
                            {"ActivityName": "Wiggle"},
                        ],
                    },
                )
            case 1:  # update description
                if self.player.get("Description"):
                    await self.update_description(self.player["Description"])
            case 2:  # update appearance
                await self.reset_appearance()
        self.logger.debug(f"keep alived using method {choice}")

    async def ChatRoomChat(self, msg, **kwargs):
        data = {"Content": msg, "Type": "Chat", "Target": None}
        data.update(kwargs)
        await self.server_send("ChatRoomChat", data)

    async def login(self, username=None, password=None):
        if not username:
            username, password = self.account
        self.logger.info(
            f"logging in using data AccountName {username}, Password: {password}"
        )
        await self.server_send(
            "AccountLogin", {"AccountName": username, "Password": password}
        )
        # TODO: use asyncio.Condition
        for wait_remaining in range(100, 0, -1):
            # check if logged in
            if not self.is_logged_in:
                self.logger.info(f"waiting for login. remaining {wait_remaining} secs")
                await asyncio.sleep(1)
            else:
                break
        if wait_remaining:  # wait_remaining == 0 means login failed
            return True
        else:
            return False

    async def try_connect(self, url, **kwargs):
        try:
            await self.sio.connect(url, **kwargs)
            return True
        except (socketio.exceptions.ConnectionError, ValueError):  # type: ignore
            return False

    async def exit_gracefully(self):
        self.is_logged_in = False
        self.player = {}
        
        for n,t in self.background_tasks.items():
            try:
                if t:
                    t.cancel()
            except:
                pass
        if self.sio:  # delete socketio client
            try:
                await self.sio.eio.disconnect()
                self.sio = None
            except:
                pass

        # self.exit_with_error(1) # TODO: 不要直接结束进程。 但是async loop 依然有问题，只能暂时通过强制退出才能结束所有协程


    # ======================================== event handlers ==============================================================

    async def ServerPlayerRelationsSync(self, playerdata):
        # from bondage club cource code in Server.js
        # print(playerdata['FriendNames'])
        self.player["FriendNames"] = self.decode_compressed_list(
            playerdata["FriendNames"]
        )
        self.player["SubmissivesList"] = set(
            self.decode_compressed_list(playerdata["SubmissivesList"])
        )
        assert isinstance(self.player["FriendNames"], dict)
        assert isinstance(self.player["SubmissivesList"], set)
        self.player["FriendNames"] = {
            k: v
            for k, v in self.player["FriendNames"].items()
            if k in self.player["FriendList"] or k in self.player["SubmissivesList"]
        }
        d = {
            "FriendList": self.player["FriendList"],
            "GhostList": self.player["GhostList"],
            "WhiteList": self.player["WhiteList"],
            "BlackList": self.player["BlackList"],
            "FriendNames": LZString.compressToUTF16(
                json.dumps(
                    list(self.player["FriendNames"].items()), separators=(",", ":")
                )
            ),
            "SubmissivesList": LZString.compressToUTF16(
                json.dumps(list(self.player["SubmissivesList"]), separators=(",", ":"))
            ),
        }
        await self.server_send("AccountUpdate", d)

    async def ChatRoomSyncCharacter(self, data):
        Characters = (
            data["Character"]
            if isinstance(data["Character"], list)
            else [data["Character"]]
        )
        for i in Characters:
            self.logger.info(f"update {i['Name']}({i['MemberNumber']})'s data")
            # self.others[i["MemberNumber"]].update(i)
            self.others[i["MemberNumber"]] = i
            # update ownership
            owner = i.get("Ownership", {})
            owner = owner.get("MemberNumber", 0) if owner else 0
            if (
                owner != 0
                and owner == self.player["MemberNumber"]
                and i["MemberNumber"] not in self.player["SubmissivesList"]
            ):
                await self.add_or_remove_submissive(i["MemberNumber"])
            # add gameversion check
            gameversion = i.get("OnlineSharedSettings", {}).get("GameVersion")
            if gameversion:
                gv = int(gameversion[1:])
                mygv = int(
                    self.player.get("OnlineSharedSettings", {}).get(
                        "GameVersion", "R0"
                    )[1:]
                )
                if gv > mygv:
                    self.player["OnlineSharedSettings"]["GameVersion"] = "R{}".format(
                        gv
                    )
                    await self.account_update({
                        "OnlineSharedSettings": self.player["OnlineSharedSettings"]
                    })

    async def ChatRoomSyncItem(self, data):
        item = data["Item"]
        if not self.others.get(item["Target"]):
            self.logger.warning(
                f"try to update an item on character {item['Target']} but the data is not in database"
            )
            return
        # update character data
        appearance = self.others[item["Target"]]["Appearance"]
        for i in range(len(appearance)):
            if appearance[i]["Group"] == item["Group"]:
                if item.get("Name"):  # change an item
                    appearance[i] = item
                else:  # remove an item
                    appearance = appearance[:i] + appearance[i + 1 :]
                return
        appearance.append(item)  # add a new item

    async def ChatRoomSync(self, data):
        self.player["LastChatRoom"] = data["Name"]
        self.player["LastChatRoomBG"] = data["Background"]
        self.current_chatroom = {
            k: v for k, v in data.items() if k not in ["Character", "Space"]
        }
        self.logger.info(
            f"entered room {data['Name']}, {len(data['Character'])} members in total"
        )
        await self.ChatRoomSyncCharacter(data)

    async def ChatRoomSyncMemberLeave(self, data):
        # del self.others[data['SourceMemberNumber']]
        pass

    async def connect(self):
        self.logger.info("connection established")

    async def disconnect(self):
        self.logger.warning(Fore.YELLOW + "disconnected from server" + Fore.RESET)
        await self.exit_gracefully()

    async def LoginResponse(self, data):
        # self.logger.debug(f"login succeed. data:{data}")
        if not isinstance(data, dict):
            data = json.loads(data)
        self.player = data
        # update friend and submissive here
        self.player["FriendNames"] = self.decode_compressed_list(
            self.player["FriendNames"]
        )
        self.player["SubmissivesList"] = set(
            self.decode_compressed_list(self.player["SubmissivesList"])
        )

        self.logger.info(f"logged in as {self.player.get('Name')}")
        self.others = defaultdict(dict)
        self.is_logged_in = True

    async def ChatRoomSearchResponse(self, data):
        self.logger.debug(f"ChatRoomSearchResponse {data}")
        if data == "JoinedRoom":
            self.inChatRoom = data

    async def AccountQueryResult(self, data):
        # join_chatroom(data['Result'][0]['ChatRoomName'])
        self.logger.info(data)

    async def ChatRoomMessage(self, data):
        await self.do_extra_actions(data)

    async def ChatRoomSyncSingle(self, data):
        await self.ChatRoomSyncCharacter(data)

    async def LoginQueue(self, data):
        await self.sio.sleep(10)
        await self.login()
    
    # self.sio.event decorator does not work inside class, so manually set it
    # another way: https://github.com/miguelgrinberg/python-socketio/issues/390#issuecomment-787796871
    
    
    def register_handlers(self):
        # register catch_all as the listener
        async def catch_all(event: str, data: dict):
            if event == "ServerInfo":
                return
            if not data or len(json.dumps(data)) > 100:
                self.logger.info(f"{event}")
            else:
                self.logger.info(f"{event},{data}")
            await self.received_event_queue.put((event,data))

        self.sio.on("*", catch_all)
        
        # should run in background with asyncio.create_task
        async def sio_event_handler():
            while True:
                # 避免被错误卡住
                try: # super big try-except! 
                    event,data = await self.received_event_queue.get()

                    useful_event = True
                    match event:
                        case "connect":
                            await self.connect()
                        case "disconnect":
                            await self.disconnect()
                        case "LoginResponse":
                            await self.LoginResponse(data)
                        case "ChatRoomSearchResponse":
                            await self.ChatRoomSearchResponse(data)
                        case "AccountQueryResult":
                            await self.AccountQueryResult(data)
                        case "ChatRoomMessage":
                            await self.ChatRoomMessage(data)
                        case "ChatRoomSync":
                            await self.ChatRoomSync(data)
                        case "ChatRoomSyncItem":
                            await self.ChatRoomSyncItem(data)
                        case "ChatRoomSyncMemberLeave":
                            await self.ChatRoomSyncMemberLeave(data)
                        case "ChatRoomSearchResult":
                            self.update_chatroom(data)
                        case "ChatRoomSyncCharacter":
                            await self.ChatRoomSyncCharacter(data)
                        case "ChatRoomSyncSingle":
                            await self.ChatRoomSyncSingle(data)
                        case "LoginQueue":
                            await self.LoginQueue(data)
                        case _:
                            useful_event = False
                            pass
                    # self.logger.info(f"handler get {event}" + " useful" if useful_event else "useless")
                    if useful_event:
                        self.last_received = time.time() # 记录最后获得有效信息的时间
                except Exception as err:
                    self.logger.error(err)

        return asyncio.create_task(sio_event_handler())
    # ======================================== end of event handlers ==============================================================


    async def run_bot(self):
        while True:
            if not self.sio:  # 执行disconnect后sio被删除，直接返回
                # print(asyncio.all_tasks())
                return False
            elif not self.sio.connected:
                if not await self.try_connect(
                    "https://bondage-club-server.herokuapp.com/",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",
                        "Origin": "https://www.bondage-europe.com",
                    },
                ):
                    self.logger.warning(Fore.YELLOW + "connection failed" + Fore.RESET)
                    await self.disconnect()
            elif not self.is_logged_in:
                # time.sleep(random.randint(5,10))
                self.logger.debug("sending login data")
                status = await self.login()
                assert status
                await self.join_or_create_chatroom(
                    self.chatroom["Name"], **self.chatroom
                )
                await asyncio.sleep(3)
                await self.reset_appearance()
                self.background_tasks['keep_alive'] = (asyncio.create_task(self.keep_alive()))
            else:
                assert self.sio.connected and self.is_logged_in
                self.logger.info(
                    "everything is done, waiting for other player's message"
                )
                await self.sio.wait()

    # ======================================== custom actions =====================================================================
    async def do_extra_actions(self, data):
        pass
