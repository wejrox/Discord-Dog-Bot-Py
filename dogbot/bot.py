""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 4.1
"""
import json
import os
import platform
import random

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import tasks, commands
from disnake.ext.commands import Bot, DefaultHelpCommand
from disnake.ext.commands import Context

from config import Config
from exceptions.permissions import UserBlacklisted
from file_references import config_location, package_dir

config: Config

if not os.path.isfile(config_location):
    print(f"'{config_location}' not found, attempting to source using environment variables...")


    def parse_owner_ids(owners: str) -> list[int]:
        """
        Splits the incoming string on comma and transforms it into integers to match what our :class:`Config` requires.

        :param owners: Comma separated string of Discord owner IDs.
        :return: A list of the owners, each represented as an int.
        """
        owners_split = owners.split(",")
        return list(map(lambda owner: int(owner), owners_split))


    config = Config(prefix=os.environ.get("BOT_PREFIX"),
                    token=os.environ.get("BOT_TOKEN"),
                    permissions=os.environ.get("BOT_PERMISSIONS"),
                    application_id=os.environ.get("BOT_APPLICATION_ID"),
                    owners=parse_owner_ids(os.environ.get("BOT_OWNERS")))
else:
    with open(config_location) as file:
        # Load in the json file as an object, then spread the resultant fields into the Config constructor.
        config = Config(**json.load(file))

"""	
Setup bot intents (events restrictions)
For more information about intents, please go to the following websites:
https://docs.disnake.dev/en/latest/intents.html
https://docs.disnake.dev/en/latest/intents.html#privileged-intents


Default Intents:
intents.bans = True
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.messages = True # `message_content` is required to get the content of the messages
intents.reactions = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True

Privileged Intents (Needs to be enabled on developer portal of Discord), please use them only if you need them:
intents.members = True
intents.message_content = True
intents.presences = True
"""

intents = disnake.Intents.default()

"""
Remove this if you don't want to use prefix (normal) commands.
It is recommended to use slash commands and therefore not use prefix commands.

If you want to use prefix commands, enable the intent below in the Discord developer portal.
"""
intents.message_content = True

bot = Bot(command_prefix=commands.when_mentioned_or(config.prefix), intents=intents,
          help_command=DefaultHelpCommand(width=120),
          token=config.token, owner_ids=config.owners)


@bot.event
async def on_ready() -> None:
    """
    The code in this even is executed when the bot is ready
    """
    print(f"Logged in as {bot.user.name}")
    print(f"disnake API version: {disnake.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")
    status_task.start()


@tasks.loop(minutes=1.0)
async def status_task() -> None:
    """
    Setup the game status task of the bot
    """
    statuses = ["in the doghouse."]
    await bot.change_presence(activity=disnake.Game(random.choice(statuses)))


def load_commands(command_type: str) -> None:
    for command_file in os.listdir(os.path.join(package_dir, "cogs", command_type)):
        if command_file.endswith(".py"):
            extension = command_file[:-3]
            try:
                bot.load_extension(f"cogs.{command_type}.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")


if __name__ == "__main__":
    """
    This will automatically load commands located in their respective folder.
    
    If you want to remove slash commands, which is not recommended due to the Message Intent being a privileged intent, 
    you can remove the loading of slash commands below.
    """
    load_commands("normal")


@bot.event
async def on_message(message: disnake.Message) -> None:
    """
    The code in this event is executed every time someone sends a message, with or without the prefix
    :param message: The message that was sent.
    """
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)


@bot.event
async def on_slash_command(interaction: ApplicationCommandInteraction) -> None:
    """
    The code in this event is executed every time a slash command has been *successfully* executed
    :param interaction: The slash command that has been executed.
    """
    print(f"Executed {interaction.data.name} command "
          f"in {interaction.guild.name} (ID: {interaction.guild.id}) "
          f"by {interaction.author} (ID: {interaction.author.id})")


@bot.event
async def on_slash_command_error(interaction: ApplicationCommandInteraction, error: Exception) -> None:
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


@bot.event
async def on_command_completion(context: Context) -> None:
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


@bot.event
async def on_command_error(context: Context, error) -> None:
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


# Run the bot with the token.
bot.run(config.token)
