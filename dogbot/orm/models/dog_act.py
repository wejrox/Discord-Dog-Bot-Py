from peewee import IntegerField, AutoField, CharField, BooleanField

from dogbot.orm.models.base_model import BaseModel


class DogAct(BaseModel):
    """
    Represents an instance in which users cast votes to determine whether a specific act should be considered dog.
    """
    id: int = AutoField()
    message_id: int = IntegerField(null=True, help_text="Unique identifier for the bot message that this relates to.")
    guild_id: int = IntegerField(help_text="Guild (discord server) that this act occurred within.")
    # TODO Swap to a one to many relationship here. Also, create the target row in the db.
    reporter: int = IntegerField(help_text="Who it was that filed this report against the target.")
    # TODO Swap to a one to many relationship here. Also, create the target row in the db.
    target: int = IntegerField(help_text="The user accused of being a dog.")
    allegation: str = CharField(
        help_text="The reason provided by the reporter as to why they should be considered a dog.")
    required_votes: int = IntegerField(
        help_text="How many votes are required in order for this dog act to be finalised for either outcome.")
    timed_out: bool = BooleanField(default=False,
                                   help_text="Whether this dog act sat idle for too long and has been cancelled.")
    found_guilty: bool = BooleanField(default=False,
                                      help_text="Whether the target was found guilty of being a dog.")
    appeal_attempted: bool = BooleanField(default=False,
                                          help_text="Whether someone has attempted to appeal this dog act before.")
    appeal_reason: str = CharField(default="",
                                   help_text="If an appeal has been attempted, why it should be considered.")
