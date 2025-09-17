import asyncio
import time
import sys
import os
import logging
import json
import random
import re
import unicodedata
from colorama import Fore
from datetime import datetime
from lzstring import LZString
import pytz
import requests

from BOT_base import BOT

if (minor:=sys.version_info[1]) < 10:
    print("不支持<3.10的版本喵，请换新版本喵")
elif minor >= 12:
    from typing import override
else:
    """
    # https://stackoverflow.com/a/13628116
    def override(method):

        async def _override(a_class):
            assert method.__name__ in a_class.__class__.__base__.__dict__ # does not support nested subclass
            return method
        return _override
    """

    def override(method):  # it does nothing though. just satisfying interpreter
        return method


class BOTNyan(BOT):
    @override
    def __init__(self, *args, **kwargs):
        self.fake_modversion = None
        self.orgasm_remaining = {} # ArousalSetting -> orgasm count 可以被改
        super().__init__(*args, **kwargs)

    @override
    async def ChatRoomSync(self, data):
        await super().ChatRoomSync(data)
        await self.fake_mod()

    async def ChatRoomSyncMemberJoin(self, data):
        await self.fake_mod(data["SourceMemberNumber"])

    @override
    async def ChatRoomSyncMemberLeave(self, data):
        if chara := data['SourceMemberNumber']:
            del self.others[chara]

    @override
    def register_handlers(self):
        self.sio.on("ChatRoomSyncMemberJoin", self.ChatRoomSyncMemberJoin)
        super().register_handlers()

    @override
    async def do_extra_actions(self, data):
        if data.get("Type") == "status":
            return
        self.logger.info(f"msg {data['Sender']}: {data['Content']}")
        await self.recognize_and_execute_command(data)

    @override
    async def reset_appearance(self):
        hour = datetime.now(pytz.timezone("Asia/Shanghai")).hour
        # change suite depend on day/night
        night = False if hour > 5 and hour < 21 else True

        appearance_day = "NobwRAcghgtgpmAXGAEgBgJwFY1gDRgDiATgPYCuADkqnAJYDmAFgC75gDCpANqcTQBE4AMyjlubAL55w0eDQDKMKN27sSFasgBCpACYBPAKqVKcfgS69+yAOpM6LBAQAKZM8RYGk4ACoGzJAA7cW4CfzMAJTgAYz49HzAvMwTENEkMmUhYBGQlFTUCDSoaXUMAGVIAd3N2Kz5BETEJMGlZHJoUKDpiADEyIJYMdTIS5C6e/tJBup4G5ABiPWWV1qy5XNRu4m0oGIBrAEYAIxHNTu3dg9nrGiWV5bX2+WQAUQM4Y7IqgGdDs7GYHen2+Pxu8zAQlE4ik6w6bw+fwBWiBiPBNkhTRhT2yL1RcCRRVGKOBPwATOjGtCWm1cZsBHQfjFiHA4GwiedkABZCgsJiU5BQ5qw56bCB0UzcAn/DmA8WSgkCzHUkV0xRMOAoWqylFuaYUIJgyxzDFC7G0jZU4XIzpwKAJY23QVYmlwvHabjkH78nWlT3epVm12imivGCkFh0OJBG1vcOR6OBl2qy3IADSjicQVeUGI5NjWx6AEEYjECT8+AYKY75sAwAsBI2wABdC3wsAZlhZ3zdbgKFjEKCUGVEYk0Ht0PsDodGzgmq3mt2bXqeuh6WfFFEr8hr2f1U3JnGpsAuNnaOAO0ecsAASScMCEADco4qazY60H2crrQRPy3XO45heIkES5CEqjhAEcDRHExCpOAyQXkg6SZCGyAuF6PwGCOm40BhPxYUmKpHu2BZFsQMA/OUIhfvuC7BmqyBkRRPyRIwrBEdabZ4gWXRBOu1HCLR87OsR3GbLxUD8ax7HCU636LmhJ5si4pA/F+uHIHecAwFyjIxAKH6HgQCxkgAzAA7AIZLVvWvRmfZ9nsAsjkOWZzm9J5AAsAAc7kmZ52gcAIABs7B/s2AGkB4wGIH4UEwfEiRaIcBCpGgBBgogFkEDASCpWAAAeyHSJCdDCMIUYwt4aThHAhVsMgHBMFJDDOGAvj1SwFLIAAmhQFgdV17noeYMCMj8dDTOwHqkNciDAJFQIVbEjWLQQKBrrk62oFt2l5QtS1Fqo1QlpGz6xTtRZdsQdDHOQThIItqGMWAADyt0MHQQQqAWZQGP2BhSpximvf9vjVHA3A4WOTW8HyhkKS0rbNkAA==="
        appearance_night = "NobwRAcghgtgpmAXGAEgBgJwFY1gDRgDiATgPYCuADkqnAJYDmAFgC75gDCpANqcTQBE4AMyjlubAL55w0eDQDKMKN27sSFasgBCpACYBPAKqVKcfgS69+yAOpM6LBAQAKZM8RYGk4ACoGzJAA7cW4CfzMAJTgAYz49HzAvMwTENEkMmUhYBGQlFTUCDSoaXUMAGVIAd3N2Kz5BETEJMGlZHJoUKDpiADEyIJYMdTIS5C6e/tJBup4G5ABiPWWV1qy5XNRu4m0oGIBrAEYAIxHNTu3dg9nrGiWV5bX2+WQAUQM4Y7IqgGdDs7GYHen2+Pxu8zAQlE4ik6w6bw+fwBWiBiPBNkhTRhT2yL1RcCRRVGKOBPwATOjGtCWm1cZsBHQfjFiHA4GwiedkABZCgsJiU5BQ5qw56bCB0UzcAn/DmA8WSgkCzHUkV0xRMOAoWqylFuaYUIJgyxzDFC7G0jZU4XIzpwKAJY23QVYmlwvHabjkH78nWlT3epVm12imivGCkFh0OJBG1vcOR6OBl2qy3IADSjicQVeUGI5NjWx6AEEYjECT8+AYKY75sAwAsBI2wABdC3wsAZlhZ3zdbgKFjEKCUGVEYk0Ht0PsDodGzgmq3mt2bMoGXzVODcEfFFEcXh8pMqnGpsC9T10PSz7c0U/kc+z+qm5NH9suNnaOAO0ecsAASScMCEAA3KNFRrGw6yDdllWtAhIJbVx3HMLxEgiXIQlUcIAjgaI4mIVJwGSD8kEOaQwAUNkXFIH5cjrItVF6Cg83gsA6N4KoS0jQC4Eo6ikFo+jGNnFBSAYSMiObAgUHPGjf3/ItiBgWc/zgGBtHILt2AnKdB0oWdbDoIIGDBCTUGk5SYD42SVK5RkYl8D9DHfXNmKkvQ4HM14AA8Yk9NzLPM+TFO0RwYiYBRbyggKFJ+YKWFC8LHC8ygqKIggosUhQHCCAxXxYBK2BMj1SGuRA63SpT/20FkoB+SLKvUuqVN6VlGtU0gIwqlTyjgIz2HMmymT6/95UoKVOpgEaxpcOhzBiAzerS/9X24YDxrXPNSCGlSADVxEAqAtpgXaVqgabZvm4zMhDZAXC9H4DC3Mcbru7wwIXYM1WQAtAp+brhCgh93pTdtvuiyJGFYA9rTbPECy6IILz+gH52dQ8Yc2OGoARn5weYZGnWgxdrrAXKeKgq9kH62yBQgp8CAWMkAGYAHYBDJat616Rmua59gFh57nGb53oRYAFgADiF+mRe0DgBAANnYOCTL1DxkMQPwsJw+JEi0Q4CFSNACDBRBmYICzEH1sBPKQdJYLoYRhCjGFvDScI4E8thkA4JgsYYZwwHsz2KWQABNRjNI9lghZu8wYEZH46GmdgipK4ATNeR3Yi99PJOkviTNc9z/wLghWOqDi6GA9Xc5YrtiDoY51Jo1t0ZoAB5BuGAMlQCxXfsDClKHzWbIA==="
        
        if not night:
            default_appearance = LZString.decompressFromBase64(
                appearance_day
            )
        else:
            default_appearance = LZString.decompressFromBase64(
                appearance_night
            )

        default_appearance = json.loads(default_appearance)  # type: ignore

        data = {
            "AssetFamily": "Female3DCG",
            "Appearance": default_appearance,
            "ItemPermission": 1,
        }
        await self.server_send("AccountUpdate", data)

    async def recognize_and_execute_command(self, data):
        if data["Type"] not in ["Chat", "Whisper", "Emote", "Activity"]:
            return
        # detect activity command
        if data["Type"] == "Activity":

            # if it is orgasm notification
            if re.match("^Orgasm[0-9]+",data['Content']):
                for i in data["Dictionary"]:
                        if (chara := i.get("SourceCharacter")) in self.orgasm_remaining:
                            # self.logger.info(f"{chara}: remaining {self.orgasm_remaining[chara]}")
                            o_remain = self.orgasm_remaining[chara]
                            o_remain -= 1
                            if o_remain <= 0:
                                del self.orgasm_remaining[chara]
                                await self.try_to_release(chara,unlock_only=True)
                            else:
                                self.orgasm_remaining[chara] = o_remain

            # if it is special action
            match data["Content"]:
                case "ChatOther-ItemHead-Rub":  # release
                    for i in data["Dictionary"]:
                        """
                        if i.get('Tag') == 'TargetCharacter':
                            if i['MemberNumber'] ==  self.player['MemberNumber']:
                        """
                        if i.get("TargetCharacter") == self.player["MemberNumber"]:
                            await self.try_to_release(data["Sender"])
                case ("ChatOther-ItemEars-Lick" | "ChatOther-ItemEars-GaggedKiss"): # take off panties
                    for i in data["Dictionary"]:
                        """
                        if i.get('Tag') == 'TargetCharacter':
                            if i['MemberNumber'] ==  self.player['MemberNumber']:
                        """
                        if i.get("TargetCharacter") == self.player["MemberNumber"]:
                            await self.take_off_pantie(data["Sender"])
            return
        help = ["救", "help"]
        help_unlock_only = ["unlock", "开锁"]
        lock_me = ["lock", "上锁"]
        myself = ["me", "我"]

        if not data["Content"]:
            return
        # if the command is eng only
        if data["Content"].isascii():
            # help command
            if not (
                result := re.findall(
                    f"^({'|'.join(help + help_unlock_only + lock_me)}) ([\w]+)",
                    data["Content"].lower(),
                )
            ):
                return
            action2, target = result[0]
            action2 = action2.lower()
            if action2 in help:
                action1 = action2
            else:
                action1 = None
        else:
            # friend request
            if (
                unicodedata.normalize("NFKC", data["Content"])
                == f"{self.player.get('Nickname') or self.player.get('Name')},你愿意做我的朋友吗?"
            ):
                if data["Sender"] not in self.player["FriendList"]:
                    await self.add_or_remove_friend(data["Sender"], add=True)
                    await self.ChatRoomChat("好喵，你已经是咱的朋友了喵!")
                else:
                    await self.ChatRoomChat("我们已经是朋友了喵!")
                return
            # lover request
            elif (
                unicodedata.normalize("NFKC", data["Content"])
                == f"{self.player.get('Nickname') or self.player.get('Name')},你愿意做我的恋人吗?"
            ):
                if data["Sender"] not in [num for num in self.player["Lovership"]]:
                    await self.become_lover(data["Sender"])
                    # await ChatRoomChat("好喵，你已经是咱的恋人了喵!")
                else:
                    await self.ChatRoomChat("我们已经是恋人了喵!")
                return
            # owner request
            elif (
                unicodedata.normalize("NFKC", data["Content"])
                == f"{self.player.get('Nickname') or self.player.get('Name')},你愿意做我的主人吗?"
            ):
                if data["Sender"] not in self.player["SubmissivesList"]:
                    await self.become_owner(data["Sender"])
                    # await ChatRoomChat("嘻嘻喵，你已经是咱的奴隶了喵!")
                else:
                    await self.ChatRoomChat("你已经是咱的奴隶了喵!")
                return
            # ownership release
            elif (
                unicodedata.normalize("NFKC", data["Content"])
                == f"{self.player.get('Nickname') or self.player.get('Name')},快放开我喵"
            ):
                await self.add_or_remove_submissive(data["Sender"], add=False)
                return
            # help command
            pattern = (
                f"^(帮|{'|'.join(help)})"
                + "(.*?)"
                + f"($|{'|'.join(lock_me + help_unlock_only)})"
            )
            if not (result := re.findall(pattern, data["Content"])):
                return
            action1, target, action2 = result[0]
        self.logger.info(
            f"data {data['Sender']}: {data['Content']} triggered action {action1} {action2} on {target}"
        )
        target = target.strip()
        if target in myself:
            target = data["Sender"]
        elif not target.isdigit():
            target = self.find_character(target)
            if not target:
                self.logger.warning(
                    "cannot find target. Resetting target to himself/herself"
                )
                target = data["Sender"]
        target = int(target)
        if action1 in help:
            await self.try_to_release(target)
        elif action2 in help_unlock_only:
            await self.try_to_release(target, unlock_only=True)
        elif action2 in lock_me:
            if target == data["Sender"]:
                await self.add_lock(target)
        else:  # default action
            await self.try_to_release(target)

    async def try_to_release(self, member_id, unlock_only=False, total_release=False):
        self.logger.info(f"try to release {member_id}")

        C = self.others.get(member_id)  # member_id argument should be int
        if not C:
            self.logger.error(Fore.RED + f"can't find {member_id}" + Fore.RESET)
            await self.ChatRoomChat(
                f"can't find player {member_id}. Using brute-force instead. 找不到你的信息喵，请检查一下是不是真的解绑了喵"
            )
            # raise AssertionError

        # check permission
        if C and not self.has_enough_permission(C):
            self.logger.warning(
                f"try to release {member_id} failed. Reason: not enough permission"
            )
            await self.ChatRoomChat(f"权限不足喵，要把物品权限打开才行喵")
            return

        # test
        # await self.fake_mod(member_id)
        # await self.fake_mod(None)

        if C and (a := C.get("Appearance")) and isinstance(a, list):
            for i in a:
                if i["Group"].startswith("Item") and i["Name"].endswith("_Luzi"): # wait, does not work?
                    self.ChatRoomChat("喵喵！发现mod服装喵，mod服装暂时解不开喵QAQ")

        if not unlock_only:
            release_method = random.randint(0, 1)
            if not C or release_method:
                self.logger.info(f"release {member_id} using new method")
                # using ChatRoomCharacterItemUpdate: release does not need Character data
                itemgroups = (
                    [
                        i["Group"]
                        for i in C["Appearance"]
                        if i["Group"].startswith("Item") and (total_release or i['Group'] != "ItemNeck")
                    ]
                    if C
                    else []
                )  # this should fall over brute force way when can't find any restraint on one character, which can avoid the
                # case that the release fails when ChatroomCharacterUpdate or self.other does not have enough information,
                #  which is caused by character updating event wrongly implemented.
                if not itemgroups:
                    itemgroups = [
                        "ItemAddon",
                        "ItemArms",
                        "ItemBoots",
                        "ItemBreast",
                        "ItemButt",
                        "ItemDevices",
                        "ItemEars",
                        "ItemFeet",
                        "ItemHandheld",
                        "ItemHands",
                        "ItemHead",
                        "ItemHood",
                        "ItemLegs",
                        "ItemMisc",
                        "ItemMouth",
                        "ItemMouth2",
                        "ItemMouth3",
                        "ItemNeck",
                        "ItemNeckAccessories",
                        "ItemNeckRestraints",
                        "ItemNipples",
                        "ItemNipplesPiercings",
                        "ItemNose",
                        "ItemPelvis",
                        "ItemScript",
                        "ItemTorso",
                        "ItemTorso2",
                        "ItemVulva",
                        "ItemVulvaPiercings"
                    ]
                for item in itemgroups:
                    await self.server_send(
                        "ChatRoomCharacterItemUpdate",
                        {
                            "Target": member_id,
                            "Group": item,
                            "Color": "default",
                            "Difficulty": 0,
                        },
                    )
                    await asyncio.sleep(0.2)  # 测试，暂停一会看看ItemUpdate还会不会卡
                                              # update: 应该是项圈触发了反弹，将项圈移到最后解除
            else:
                # old way to release
                self.logger.info(f"release {member_id} using old method")
                appearance = C["Appearance"]
                appearance = [
                    i
                    for i in appearance
                    if (not total_release and i["Group"] == "ItemNeck")
                    or not i["Group"].startswith("Item")
                ]
                assert await self.update_appearance(member_id, appearance)

        # unlock only
        else:
            if not C:
                self.logger.error(
                    Fore.RED
                    + "cannot unlock {member_id} because can't find this the character"
                    + Fore.RESET
                )
                return
            appearance = (
                C["Appearance"]
                if C and isinstance(C["Appearance"], list)
                else json.loads(C["Appearance"])
            )
            # ValidationAllLockProperties from Bondage-Club source code
            lock_properties = (
                ["LockedBy", "LockMemberNumber"]
                + [
                    "EnableRandomInput",
                    "RemoveItem",
                    "ShowTimer",
                    "CombinationNumber",
                    "Password",
                    "Hint",
                    "LockSet",
                    "LockPickSeed",
                ]
                + ["MemberNumberList", "RemoveTimer"]
            )

            # inline edit
            for item in appearance:
                if (
                    item["Group"].startswith("Item")
                    and item.get("Property")
                    and item.get("Property").get("LockedBy")
                ):
                    # ValidationDeleteLock from Bondage-Club source code
                    for lockproperty in lock_properties:
                        if item["Property"].get(lockproperty):
                            del item["Property"][lockproperty]
                    if isinstance(item["Property"]["Effect"], list) and item[
                        "Property"
                    ].get("Effect"):
                        item["Property"]["Effect"].remove("Lock")

                assert await self.update_appearance(C["ID"], appearance)
        """
        # old way to release
        else:
            appearance = [i for i in appearance if 
                (not total_release and i['Group'] == "ItemNeck") 
                or not i['Group'].startswith("Item")
            ]
        """
        # assert update_appearance(C['ID'], appearance)
        if unlock_only:
            self.logger.info(f"unlocked {member_id}")
        else:
            self.logger.info(f"helped {member_id}")

        self_arm_restrainted = False
        if self.is_arm_restrainted(self.player["MemberNumber"]) or False:
            self_arm_restrainted = True
        subject_text = (
            f"{self.player.get('Nickname') or self.player.get('Name')}"
            if not self_arm_restrainted
            else f"尽管被绑着，但{self.player.get('Nickname') or self.player.get('Name')}还是"
        )

        character_name = C.get("Nickname") or C.get("Name") if C else member_id
        if unlock_only:
            action_text = f"帮{character_name}打开了身上的锁"
            # ChatRoomChat("custom bot talk",Type="Action",Dictionary=[{"Tag":"MISSING PLAYER DIALOG: custom bot talk","Text":f"BOT帮{C.get('Nickname') or C.get('Name')}打开了身上的锁"}])
        else:
            if self.player and member_id == self.player.get("MemberNumber"):
                return
            else:
                action_text = f"帮{character_name}解开了束缚"
                # ChatRoomChat("custom bot talk",Type="Action",Dictionary=[{"Tag":"MISSING PLAYER DIALOG: custom bot talk","Text":f"BOT帮{C.get('Nickname') or C.get('Name')}解开了束缚"}])
        # await self.ChatRoomChat("custom bot talk",Type="Action",Dictionary=[{"Tag":"MISSING PLAYER DIALOG: custom bot talk","Text":subject_text+action_text}])
        # await self.ChatRoomChat(f"helped {character_name}",Type="Emote",Dictionary=[{"Tag":"MISSING PLAYER DIALOG: custom bot talk","Text":subject_text+action_text}])
        # await self.ChatRoomChat(f"helped {member_id} using method {release_method+1}",Type="Emote")
        await self.ChatRoomChat("*" + subject_text + action_text, Type="Emote")

    async def add_lock(self, member_id,until_orgasm=0):
        self.logger.info(f"try to add lock to {member_id}")
        C = self.others.get(member_id, {})
        appearance = C.get("Appearance")
        if not C or not appearance:
            self.logger.warning("cannot find character")
            await self.ChatRoomChat(
                f"can't find player {member_id}. Re-entering the room may help. 找不到你的信息喵，麻烦重进一下聊天室喵"
            )
            return

        appearance = (
            appearance if isinstance(appearance, list) else json.loads(appearance)
        )

        use_pandora_lock = random.randint(1, 10) == 1
        for item in appearance:
            if item["Group"].startswith("Item"):
                # add lock
                logging.debug(f"found {item}")
                new_property = {
                    "Effect": item.get("Property", {}).get("Effect", []) + ["Lock"],
                    "LockedBy": "PandoraPadlock"
                    if use_pandora_lock
                    else "ExclusivePadlock",
                    "LockMemberNumber": self.player["MemberNumber"],
                }
                if item.get("Property") and isinstance(item["Property"], dict):
                    item["Property"].update(new_property)
                else:
                    item["Property"] = new_property

        await self.update_appearance(C["ID"], appearance, pose=C.get("ActivePose"))
        await self.ChatRoomChat(
            f"*BOT帮{C.get('Nickname') or C.get('Name')}的道具都加上了锁", Type="Emote"
        )
        # unlock after n times of orgasms
        if until_orgasm:
            self.orgasm_remaining[member_id] = until_orgasm


    async def take_off_pantie(self, member_id):
        self.logger.info(f"try to take off pantie from {member_id}")
        C = self.others.get(member_id, {})
        appearance = C.get("Appearance")
        if not C or not appearance:
            self.logger.warning("cannot find character {}".format(member_id))
            return

        appearance = [i for i in appearance if i["Group"] != "Panties"]
        await self.update_appearance(C["ID"], appearance, pose=C.get("ActivePose"))
        await self.ChatRoomChat(
            f"*BOT把{C.get('Nickname') or C.get('Name')}的胖次脱掉了", Type="Emote"
        )

    async def fake_mod(self, target=None):
        '''伪造[服装拓展](https://github.com/SugarChain-Studio/echo-clothing-ext)的广播，让bot能解除服装扩展的衣服'''
        
        """ sample mod broadcast
        [
            "ChatRoomMessage",
            {
                "Sender": 118180,
                "Content": "ECHO_INFO2",
                "Type": "Hidden",
                "Dictionary": [
                    {
                        "Type": "ECHO_INFO2",
                        "Content": {
                            "æè£æå±": {
                                "version": "1.45.0-beta",
                                "beta": true
                            },
                            "å¨ä½æå±": {
                                "version": "0.14.1-beta",
                                "beta": true
                            }
                        }
                    }
                ]
            }
        ]
        """

        ECHO_INFO_TAG = "ECHO_INFO2"

        # init mod version
        if not self.fake_modversion:
            fake_modversion = {
                "服装拓展": {"version": "1.44.0", "beta": False},
                "动作拓展": {"version": "0.14.2", "beta": False},
            }

            # updating version number
            for i, u in zip(
                fake_modversion,
                [
                    "https://sugarchain-studio.github.io/echo-clothing-ext/bc-cloth.js",
                    "https://sugarchain-studio.github.io/echo-activity-ext/bc-activity.user.js",
                ],
            ):
                fake_modversion[i]["version"] = (
                    found[1]
                    if (
                        found := re.search(
                            'version:"([0-9.]+)"',
                            (await asyncio.to_thread(requests.get, u)).text,
                        )
                    )
                    else fake_modversion[i]["version"]
                )

            self.fake_modversion = fake_modversion

        # https://github.com/SugarChain-Studio/bc-modding-utilities/blob/765e732eb9a9ef6aafcf984d1bf046f248dd602a/src/charaTag.js#L23
        await self.ChatRoomChat(
            ECHO_INFO_TAG,
            Type="Hidden",
            Dictionary=[{"Type": ECHO_INFO_TAG, "Content": self.fake_modversion}],
            **(
                {"Target": target} if target else {}
            ),  # if target is not set then no target argument
        )


def stop_all():
    for task in asyncio.all_tasks():
        try:
            task.cancel()
        finally:
            pass


async def main():
    # https://www.geeksforgeeks.org/how-to-log-python-messages-to-both-stdout-and-files/
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)s:%(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "file1": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": f"log/{int(time.time())}-bot1.log",
                "formatter": "default",
            },
            "file2": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": f"log/{int(time.time())}-bot2.log",
                "formatter": "default",
            },
            "stdout": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "logger1": {
                "handlers": ["file1", "stdout"],
                "level": "DEBUG",
                "propagate": True,
            },
            "logger2": {
                "handlers": ["file2", "stdout"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)

    bots = [
        BOTNyan(
            username="bot1",
            password="123",
            chatroom={
                "Name": "auto release room",
                "Description": "bot自动解绑喵，详情看bio喵",
                "Space": "",
                "Background": "Onsen"
            },
            logger=logging.getLogger("logger1"),
        ),
        BOTNyan(
            username="bot2",
            password="456",
            chatroom={
                "Name": "auto release beta",
                "Description": "say 'help me'",
                "Space": "X",
                "Background": "Onsen"
            },
            logger=logging.getLogger("logger2"),
        ),
    ]

    tasks = []
    for b in bots:
        tasks.append(asyncio.create_task(b.run_bot()))

    while True:
        if any(t.done() for t in tasks):  # the task should not be done
            print("something wrong with the bot")
            break
        await asyncio.sleep(60)
    # asyncio.gather(*asyncio.all_tasks())
    print(
        "unless intended, the bot is stopped unexpectedly. please check your config and connection"
    )


if __name__ == "__main__":
    
    try:
        import gzip
        import shutil
        for f in os.listdir("log"):
            if f.endswith("log"):
                f = "log/" + f
                f_c = f + ".gz"
                with gzip.open(f_c,"wb") as compressed, open(f,"rb") as fin:
                    shutil.copyfileobj(fin,compressed)
                os.remove(f)
    except:
        pass

    try:
        asyncio.run(main())
    except:
        pass
