from dataclasses import dataclass


@dataclass
class Config:
    """
    Global configuration for the bot. This is attached to the bot once it's created, and accessible through context.
    """
    prefix: str  #: Prefix that users should use to execute commands.
    token: str  #: Secret token for the bot to use when authenticating with Discord.
    permissions: str  #: Permissions integer representing required permissions the bot needs on the server. UNUSED.
    application_id: str  #: Developer application that this bot belongs to. UNUSED.
    owners: list[int]  #: Unique user IDs of Discord users that have ownership over the bot.
