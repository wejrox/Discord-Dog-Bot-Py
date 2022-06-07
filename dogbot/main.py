import os
import sys

import disnake
from disnake.ext import commands
from disnake.ext.commands import DefaultHelpCommand

from dogbot.config import Config
from dogbot.extensions.dog_bot import DogBot


def main(config: Config):
    """
    Runs the bot, loading in commands and applying config.
    :param config: Configuration options to apply to the bot.
    """
    # Validate that what we need is available.
    try:
        config.validate()
    except (FileNotFoundError, ValueError) as e:
        print(e)
        sys.exit(1)

    # Since we're using prefixed commands (not slash) we need to declare our intent.
    intents = disnake.Intents.default()
    intents.message_content = True

    bot = DogBot(command_prefix=commands.when_mentioned_or(config.prefix), intents=intents,
                 help_command=DefaultHelpCommand(width=120),
                 token=config.token, owner_ids=config.owners, config=config)

    # Load the bot commands This finds any files in the cogs folder adjacent to where this file is located, and sources.
    for command_file in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
        # Load in any python files that aren't metadata files.
        if command_file.endswith('.py') and not command_file.startswith('__'):
            command_file = command_file[:-3]
            try:
                # This needs to be the location of the cog as if you were to import it.
                bot.load_extension(f'dogbot.cogs.{command_file}')
                print(f'Loaded extension "{command_file}"')
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f'Failed to load extension {command_file}\n{exception}')

    # Run the bot with the token.
    bot.run(config.token)
