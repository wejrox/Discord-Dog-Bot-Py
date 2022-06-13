from peewee import ForeignKeyField

from orm.models.base_model import BaseModel
from orm.models.dog_act import DogAct
from orm.models.member import Member


class YesVote(BaseModel):
    """
    A 'yes' vote on a specified :class:`DogAct`, from the attached :class:`Member`.
    """
    dog_act = ForeignKeyField(DogAct, help_text='Dog act being voted upon.')
    member = ForeignKeyField(Member, help_text='Discord member that cast this vote.')


class NoVote(BaseModel):
    """
    A 'no' vote on a specified :class:`DogAct`, from the attached :class:`Member`.
    """
    dog_act = ForeignKeyField(DogAct, help_text='Dog act being voted upon.')
    member = ForeignKeyField(Member, help_text='Discord member that cast this vote.')
