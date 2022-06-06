""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 4.1
"""

import json
from typing import TypeVar, Callable

from disnake.ext import commands

from exceptions.permissions import UserNotOwner, UserBlacklisted
from file_references import blacklist_location

T = TypeVar("T")


def is_owner() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is an owner of the bot.
    """

    async def predicate(context: commands.Context) -> bool:
        if context.author.id not in context.bot.owner_ids:
            raise UserNotOwner
        return True

    return commands.check(predicate)


def not_blacklisted() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is blacklisted.
    """

    async def predicate(context: commands.Context) -> bool:
        with open(blacklist_location) as file:
            data = json.load(file)
        if context.author.id in data["ids"]:
            raise UserBlacklisted
        return True

    return commands.check(predicate)
