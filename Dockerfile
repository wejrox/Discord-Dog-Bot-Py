FROM python:alpine3.16

WORKDIR /opt/python-bot

# Copy in early to cache installed packages and reduce build times.
COPY requirements.txt ./requirements.txt
RUN python3 -m pip install -r requirements.txt

# Copy in order of least to most likely to change.
COPY dogbot/exceptions ./exceptions
COPY dogbot/helpers ./helpers
COPY dogbot/cogs ./cogs
COPY dogbot/bot.py ./bot.py

# Prefix to use when issuing commands.
ENV BOT_PREFIX = "UNSET_PREFIX"

# Secret token for the bot.
ENV BOT_TOKEN = "UNSET_TOKEN"

# Permissions integer representing required permissions the bot needs on the server.
ENV BOT_PERMISSIONS = "UNSET_PERMISSIONS"

# Application that this bot is a part of.
ENV BOT_APPLICATION_ID = "UNSET_APPLICATION ID"

# Comma separated list of user IDs that have ownership over the bot.
ENV BOT_OWNERS = "UNSET_OWNERS,SEPARATED_BY_COMMA"

CMD ["python3", "bot.py"]
