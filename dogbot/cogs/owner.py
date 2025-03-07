""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 4.1
"""

import json

import disnake
from disnake.ext import commands
from disnake.ext.commands import Context

from dogbot.helpers import json_manager, checks


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="shutdown",
        description="Make the bot shutdown.",
        hidden=True
    )
    @checks.is_owner()
    async def shutdown(self, context: Context):
        """
        Makes the bot shutdown.
        """
        embed = disnake.Embed(
            description="Shutting down. Bye! :wave:",
            color=0x9C84EF
        )
        await context.send(embed=embed)
        await self.bot.close()

    @commands.command(
        name="say",
        description="The bot will say anything you want.",
        hidden=True
    )
    @checks.is_owner()
    async def say(self, context: Context, *, message: str):
        """
        The bot will say anything you want.
        """
        await context.send(message)

    @commands.command(
        name="embed",
        description="The bot will say anything you want, but within embeds.",
        hidden=True
    )
    @checks.is_owner()
    async def embed(self, context: Context, *, message: str):
        """
        The bot will say anything you want, but within embeds.
        """
        embed = disnake.Embed(
            description=message,
            color=0x9C84EF
        )
        await context.send(embed=embed)

    @commands.group(
        name="blacklist",
        hidden=True
    )
    async def blacklist(self, context: Context):
        """
        Lets you add or remove a user from not being able to use the bot.
        """
        if context.invoked_subcommand is None:
            blacklist_file = context.bot.config.blacklist_file_location
            with open(blacklist_file) as file:
                blacklist = json.load(file)
            embed = disnake.Embed(
                title=f"There are currently {len(blacklist['ids'])} blacklisted IDs",
                description=f"{', '.join(str(user_id) for user_id in blacklist['ids'])}",
                color=0x9C84EF
            )
            await context.send(embed=embed)

    @blacklist.command(
        name="add",
        hidden=True
    )
    async def blacklist_add(self, context: Context, member: disnake.Member = None):
        """
        Lets you add a user from not being able to use the bot.
        """
        try:
            user_id = member.id
            blacklist_file = context.bot.config.blacklist_file_location
            with open(blacklist_file) as file:
                blacklist = json.load(file)
            if user_id in blacklist['ids']:
                embed = disnake.Embed(
                    title="Error!",
                    description=f"**{member.name}** is already in the blacklist.",
                    color=0xE02B2B
                )
                return await context.send(embed=embed)
            json_manager.add_user_to_blacklist(blacklist_file, user_id)
            embed = disnake.Embed(
                title="User Blacklisted",
                description=f"**{member.name}** has been successfully added to the blacklist",
                color=0x9C84EF
            )
            with open(blacklist_file) as file:
                blacklist = json.load(file)
            embed.set_footer(
                text=f"There are now {len(blacklist['ids'])} users in the blacklist"
            )
            await context.send(embed=embed)
        except:
            embed = disnake.Embed(
                title="Error!",
                description=f"An unknown error occurred when trying to add **{member.name}** to the blacklist.",
                color=0xE02B2B
            )
            await context.send(embed=embed)

    @blacklist.command(
        name="remove",
        hidden=True
    )
    async def blacklist_remove(self, context, member: disnake.Member = None):
        """
        Lets you remove a user from not being able to use the bot.
        """
        try:
            user_id = member.id
            blacklist_file = context.bot.config.blacklist_file_location
            json_manager.remove_user_from_blacklist(blacklist_file, user_id)
            embed = disnake.Embed(
                title="User removed from blacklist",
                description=f"**{member.name}** has been successfully removed from the blacklist",
                color=0x9C84EF
            )
            with open(blacklist_file) as file:
                blacklist = json.load(file)
            embed.set_footer(
                text=f"There are now {len(blacklist['ids'])} users in the blacklist"
            )
            await context.send(embed=embed)
        except:
            embed = disnake.Embed(
                title="Error!",
                description=f"**{member.name}** is not in the blacklist.",
                color=0xE02B2B
            )
            await context.send(embed=embed)


def setup(bot):
    bot.add_cog(Owner(bot))
