from peewee import DatabaseProxy

# Store a reference to the database used by this bot.
# This proxy must be set before it can be used, see the main entrypoint for reference.
dog_bot_database_proxy = DatabaseProxy()
