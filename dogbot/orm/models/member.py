from peewee import IntegerField

from orm.models.base_model import BaseModel


class Member(BaseModel):
    """
    Representation of a Discord member.
    """
    id: int = IntegerField(primary_key=True, help_text="Unique user identifier for this Member, as present in Discord")

