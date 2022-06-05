""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 4.1
"""

import platform
import random

import disnake
from disnake import Member
from disnake.ext import commands
from disnake.ext.commands import Context, Bot

from helpers import checks


class General(commands.Cog, name="general"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @commands.command(
        name="botinfo",
        description="Get some useful (or not) information about the bot.",
    )
    @checks.not_blacklisted()
    async def botinfo(self, context: Context) -> None:
        """
        Get some useful (or not) information about the bot.
        :param context: The context in which the command has been executed.
        """
        embed = disnake.Embed(
            description="Created using [Krypton's](https://krypton.ninja) template",
            color=0x9C84EF
        )
        embed.set_author(
            name="Dog Bot Information"
        )
        owners: [Member] = []
        for owner_id in self.bot.owner_ids:
            owners.append(await context.guild.get_or_fetch_member(owner_id))
        embed.add_field(
            name="Owner(s):",
            value=", ".join(list(map(lambda owner: owner.name, owners))),
            inline=True
        )
        embed.add_field(
            name="Python Version:",
            value=f"{platform.python_version()}",
            inline=True
        )
        embed.add_field(
            name="Command Prefix(es):",
            value=", ".join(self.bot.command_prefix(self.bot, "")),
            inline=False
        )
        general_commands = filter(lambda command: not command.hidden, self.bot.commands)
        embed.add_field(
            name="Commands Available",
            value=", ".join(list(map(lambda command: command.name, general_commands))),
            inline=False
        )
        embed.set_footer(
            text=f"Requested by {context.author}"
        )
        await context.send(embed=embed)

    @commands.command(
        name="ping",
        description="Check if the bot is alive.",
    )
    @checks.not_blacklisted()
    async def ping(self, context: Context) -> None:
        """
        Check if the bot is alive.
        :param context: The context in which the command has been executed.
        """
        embed = disnake.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0x9C84EF
        )
        await context.send(embed=embed)

    @commands.command(
        name="8ball",
        description="Ask any question to the bot.",
    )
    @checks.not_blacklisted()
    async def eight_ball(self, context: Context, *, question: str) -> None:
        """
        Ask any question to the bot.
        :param context: The context in which the command has been executed.
        :param question: The question that should be asked by the user.
        """
        answers = ["It is certain.", "It is decidedly so.", "You may rely on it.", "Without a doubt.",
                   "Yes - definitely.", "As I see, yes.", "Most likely.", "Outlook good.", "Yes.",
                   "Signs point to yes.", "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
                   "Cannot predict now.", "Concentrate and ask again later.", "Don't count on it.", "My reply is no.",
                   "My sources say no.", "Outlook not so good.", "Very doubtful."]
        embed = disnake.Embed(
            title="**My Answer:**",
            description=f"{random.choice(answers)}",
            color=0x9C84EF
        )
        embed.set_footer(
            text=f"The question was: {question}"
        )
        await context.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
