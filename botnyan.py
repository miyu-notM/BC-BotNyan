import asyncio
import time
import sys
import logging
import json
import random
import re
import unicodedata
from colorama import Fore

from BOT_base import BOT


if sys.version_info[1] >= 12:
    from typing import override
else:

    def override(method):  # it does nothing though. just satisfying interpreter
        return method


class BOTNyan(BOT):
    @override
    async def do_extra_actions(self, data):
        if data.get("Type") == "status":
            return
        await self.recognize_and_execute_command(data)

    async def recognize_and_execute_command(self, data):
        if data["Type"] not in ["Chat", "Whisper", "Emote", "Activity"]:
            return
        # detect activity command
        if data["Type"] == "Activity":
            match data["Content"]:
                case "ChatOther-ItemHead-Rub":  # release
                    for i in data["Dictionary"]:
                        if i.get("TargetCharacter") == self.player["MemberNumber"]:
                            await self.try_to_release(data["Sender"])
                case (
                    "ChatOther-ItemEars-Lick" | "ChatOther-ItemEars-GaggedKiss"
                ):  # | "ChatOther-ItemArms-Cuddle":
                    for i in data["Dictionary"]:
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
        logging.info(
            f"data {data['Sender']}: {data['Content']} triggered action {action1} {action2} on {target}"
        )
        target = target.strip()
        if target in myself:
            target = data["Sender"]
        elif not target.isdigit():
            target = self.find_character(target)
            if not target:
                logging.warning(
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
        logging.info(f"try to release {member_id}")

        C = self.others.get(member_id)  # member_id argument should be int
        if not C:
            logging.error(Fore.RED + f"can't find {member_id}" + Fore.RESET)
            await self.ChatRoomChat(
                f"can't find player {member_id}. Using brute-force instead. 找不到你的信息喵，请检查一下是不是真的解绑了喵"
            )
            # raise AssertionError

        # check permission
        if C and not self.has_enough_permission(C):
            logging.warning(
                f"try to release {member_id} failed. Reason: not enough permission"
            )
            await self.ChatRoomChat(f"权限不足喵，要把物品权限打开才行喵")
            return

        if not unlock_only:
            release_method = random.randint(0, 1)
            if not C or release_method:
                logging.info(f"release {member_id} using new method")
                # using ChatRoomCharacterItemUpdate: release does not need Character data
                itemgroups = (
                    [
                        i["Group"]
                        for i in C["Appearance"]
                        if i["Group"].startswith("Item")
                    ]
                    if (C and not total_release)
                    else []
                )  # this should fall over brute force way when can't find any restraint on one character, which can avoid the
                # case that the release fails when ChatroomCharacterUpdate or self.other does not have enough information,
                #  which is caused by character updating event wrongly implemented.
                if not itemgroups:
                    itemgroups = [
                        "ItemFeet",
                        "ItemLegs",
                        "ItemVulva",
                        "ItemVulvaPiercings",
                        "ItemButt",
                        "ItemPelvis",
                        "ItemTorso",
                        "ItemTorso2",
                        "ItemNipples",
                        "ItemNipplesPiercings",
                        "ItemBreast",
                        "ItemArms",
                        "ItemHands",
                        "ItemHandheld",
                        "ItemNeck",
                        "ItemNeckAccessories",
                        "ItemNeckRestraints",
                        "ItemMouth",
                        "ItemMouth2",
                        "ItemMouth3",
                        "ItemHead",
                        "ItemNose",
                        "ItemHood",
                        "ItemEars",
                        "ItemMisc",
                        "ItemDevices",
                        "ItemAddon",
                        "ItemBoots",
                        "ItemScript",
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
            else:
                # old way to release
                logging.info(f"release {member_id} using old method")
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
                logging.error(
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

        if unlock_only:
            logging.info(f"unlocked {member_id}")
        else:
            logging.info(f"helped {member_id}")

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
        else:
            if self.player and member_id == self.player.get("MemberNumber"):
                return
            else:
                action_text = f"帮{character_name}解开了束缚"
        # await self.ChatRoomChat(f"helped {member_id} using method {release_method+1}",Type="Emote")
        await self.ChatRoomChat(subject_text + action_text, Type="Emote")

    async def add_lock(self, member_id):
        logging.info(f"try to add lock to {member_id}")
        C = self.others.get(member_id, {})
        appearance = C.get("Appearance")
        if not C or not appearance:
            logging.warning("cannot find character")
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

    async def take_off_pantie(self, member_id):
        logging.info(f"try to take off pantie from {member_id}")
        C = self.others.get(member_id, {})
        appearance = C.get("Appearance")
        if not C or not appearance:
            logging.warning("cannot find character {}".format(member_id))
            return

        appearance = [i for i in appearance if i["Group"] != "Panties"]
        await self.update_appearance(C["ID"], appearance, pose=C.get("ActivePose"))
        await self.ChatRoomChat(
            f"*BOT把{C.get('Nickname') or C.get('Name')}的胖次脱掉了", Type="Emote"
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
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": f"log/{int(time.time())}-bot.log",
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
                "handlers": ["file", "stdout"],
                "level": "DEBUG",
                "propagate": True,
            }
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)

    # modify it
    # add it here if you have multiple bot
    bots = [
        BOTNyan(
            username="botnyan",
            password="123456",
            chatroom={
                "Name": "auto release beta",
                "Description": "say 'help me'",
                "Space": "X",
            },
            logger=logging.getLogger("logger1"),
        )
    ]

    tasks = []
    for b in bots:
        tasks.append(asyncio.create_task(b.run_bot()))

    while True:
        if any(t.done() for t in tasks):  # the task should not be done
            print("something wrong with the bot")
            break
        await asyncio.sleep(1)
    print(
        "unless intended, the bot is stopped unexpectedly. please check your config and connection"
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        # stop_all()
        pass
