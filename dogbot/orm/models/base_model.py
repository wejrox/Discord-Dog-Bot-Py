from peewee import Model

from orm.database import dog_bot_database


class BaseModel(Model):
    """
    The base model for all Dog Bot models. A centralised place where the database to use is determined.
    """

    class Meta:
        """
        Tell this model and all child models to use the db defined globally.
        """
        database = dog_bot_database
