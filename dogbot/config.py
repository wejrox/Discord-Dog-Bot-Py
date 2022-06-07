import dataclasses
import json
import os
from dataclasses import dataclass, field
from os.path import dirname
from typing import List


@dataclass
class Config:
    """
    Global configuration for the bot. This is used for all bot communications with Discord, and file location sourcing.
    """
    prefix: str = ""
    """Prefix that users should use to execute commands."""
    token: str = ""
    """Secret token for the bot to use when authenticating with Discord."""
    owners: List[int] = field(default_factory=list)
    """Unique user IDs of Discord users that have ownership over the bot."""
    permissions: str = ""
    """DEPRECATED Permissions integer representing required permissions the bot needs on the server."""
    application_id: str = ""
    """DEPRECATED Developer application that this bot belongs to."""

    merge_with_config_file: bool = False
    """Whether the command line arguments should be merged on top of the configuration file."""
    config_file_location: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    """Path to the optional config file to merge the command line arguments into."""

    # These should change to be automatically generated by the app within a user-defined database folder location.
    blacklist_file_location: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database',
                                                'blacklist.json')
    """Path to the blacklist file for restricting access."""
    database_file_location: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'dog_bot.db')
    """Path to the database file for storing data."""

    def validate(self) -> None:
        """
        Validates that this config object is usable by the bot.

        :raises: If anything is invalid, providing a useful message.
        """
        if not os.path.isdir(dirname(self.database_file_location)):
            raise FileNotFoundError("Database file directory doesn't exist."
                                    " Use '--help' for more information.")
        if not os.path.isfile(self.blacklist_file_location):
            raise FileNotFoundError(
                f"Blacklist file doesn't exist at the provided path '{self.blacklist_file_location}'."
                f" Use '--help' for more information.")
        if not self.token:
            raise ValueError("A token was not provided, but one is required in order to validate with Discord."
                             " Use '--help' for more information.")


def source_and_merge_base_config(latest_config: Config) -> Config:
    """
    Attempts to source the config file specified, and merge that into the existing config.

    :param latest_config: config to use as a source of truth.
    :return: A Config that has been merged into the base config defined within config.
    :raises: if config file cannot be found.
    """
    if not os.path.isfile(latest_config.config_file_location):
        raise FileNotFoundError(
            f"'{latest_config.config_file_location}' could not found, but we have been told to source it."
            f" Bot won't start to prevent unwanted behaviour.")
    with open(latest_config.config_file_location) as file:
        # Use any fields from the CLI args, falling back to those in the config file if they weren't set.
        return _merge_config_with_base(Config(**json.load(file)), latest_config)


def _merge_config_with_base(base_config: Config, new_config: Config) -> Config:
    """
    Merges the new config into the base config, preferring any values in new config that aren't falsy.

    :param base_config: Config to use as a base.
    :param new_config: Config to use as a source of truth. Non-falsy values will persist in the resultant Config.
    :return: A new merged config.
    """
    # Generating the config as a dict prevents the developer from having to update it as config properties change.
    merged_config = dataclasses.replace(base_config).__dict__
    new_config_dict = new_config.__dict__

    # Merged config will use the new config entries when they are filled in, otherwise falls back to the base config
    # values that it was defined with.
    for config_field in new_config_dict:
        if new_config_dict[config_field]:
            merged_config[config_field] = new_config_dict[config_field]

    # Create a new config object by spreading our merged object as args.
    return Config(**merged_config)
