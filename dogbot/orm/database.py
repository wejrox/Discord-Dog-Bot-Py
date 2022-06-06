from peewee import SqliteDatabase

from file_references import database_location

# Store a reference to the database used by this bot.
dog_bot_database = SqliteDatabase(database_location)
