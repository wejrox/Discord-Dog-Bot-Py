import os
import platform
import random

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands, tasks
from disnake.ext.commands import Context, Bot
from peewee import SqliteDatabase

from dogbot.config import Config
from dogbot.exceptions.permissions import UserBlacklisted
from dogbot.orm.database import dog_bot_database_proxy


class DogBot(Bot):
    """
    Extension of the :class:`disnake.Bot` class which adds custom logic.
    A complete substitute for the :class:`disnake.Bot` class.
    """

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config

        # We use a proxy db because we don't know where the db may be located.
        # This allows us to define the database location at runtime.
        dog_bot_database_proxy.initialize(SqliteDatabase(config.database_file_location))

    @tasks.loop(minutes=1.0)
    async def status_task(self) -> None:
        """
        Update the game status task of the bot
        """
        statuses = ["in the doghouse."]
        await self.change_presence(activity=disnake.Game(random.choice(statuses)))

    async def on_ready(self) -> None:
        """
        The code in this even is executed when the bot is ready.
        https://docs.disnake.dev/en/latest/api.html#disnake.on_ready
        """
        print(f"Logged in as {self.user.name}")
        print(f"disnake API version: {disnake.__version__}")
        print(f"Python version: {platform.python_version()}")
        print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        print("-------------------")
        self.status_task.start()

    async def on_message(self, message: disnake.Message) -> None:
        """
        Called when any :class:`disnake.Message` is created and sent within a server this
        :class:`disnake.ext.commands.Bot` is part of.
        `Docs <https://docs.disnake.dev/en/latest/api.html#disnake.on_message>`_

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_slash_command(self, interaction: ApplicationCommandInteraction) -> None:
        """
        The code in this event is executed every time a slash command has been *successfully* executed.
        :param interaction: The slash command that has been executed.
        """
        print(f"Executed {interaction.data.name} command "
              f"in {interaction.guild.name} (ID: {interaction.guild.id}) "
              f"by {interaction.author} (ID: {interaction.author.id})")

    async def on_slash_command_error(self, interaction: ApplicationCommandInteraction, error: Exception) -> None:
        """
        The code in this event is executed every time a valid slash command catches an error
        :param interaction: The slash command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, UserBlacklisted):
            """
            The code here will only execute if the error is an instance of 'UserBlacklisted', which can occur when using
            the @checks.is_owner() check in your command, or you can raise the error by yourself.

            'hidden=True' will make so that only the user who execute the command can see the message
            """
            embed = disnake.Embed(
                title="Error!",
                description="You are blacklisted from using the bot.",
                color=0xE02B2B
            )
            print("A blacklisted user tried to execute a command.")
            return await interaction.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.errors.MissingPermissions):
            embed = disnake.Embed(
                title="Error!",
                description="You are missing the permission(s) `" + ", ".join(
                    error.missing_permissions) + "` to execute this command!",
                color=0xE02B2B
            )
            print("A blacklisted user tried to execute a command.")
            return await interaction.send(embed=embed, ephemeral=True)
        raise error

    async def on_command_completion(self, context: Context) -> None:
        """
        The code in this event is executed every time a normal command has been *successfully* executed
        :param context: The context of the command that has been executed.
        """
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        print(f"Executed {executed_command} command "
              f"in {context.guild.name} (ID: {context.message.guild.id}) "
              f"by {context.message.author} (ID: {context.message.author.id})")

    async def on_command_error(self, context: Context, error) -> None:
        """
        The code in this event is executed every time a normal valid command catches an error
        :param context: The normal command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = disnake.Embed(
                title="Hey, please slow down!",
                description=f"You can use this command again in "
                            f"{f'{round(hours)} hours' if round(hours) > 0 else ''} "
                            f"{f'{round(minutes)} minutes' if round(minutes) > 0 else ''} "
                            f"{f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(
                title="Error!",
                description="You are missing the permission(s) `"
                            f"{', '.join(error.missing_permissions)}"
                            "` to execute this command!",
                color=0xE02B2B
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(
                title="Error!",
                # We need to capitalize because the command arguments have no capital letter in the code.
                description=str(error).capitalize(),
                color=0xE02B2B
            )
            await context.send(embed=embed)
        raise error
