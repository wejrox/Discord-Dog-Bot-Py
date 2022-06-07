FROM python:alpine3.16 as base

WORKDIR /opt/python-bot

# Copy in early to cache installed packages and reduce build times.
COPY build_requirements.txt ./build_requirements.txt
COPY requirements.txt ./requirements.txt
RUN python3 -m pip install -r requirements.txt -r build_requirements.txt

# We need setup.py in order to install from source.
COPY setup.py ./setup.py

# Copy in the source.
COPY dogbot/ ./dogbot/

# Install the module.
RUN python3 setup.py bdist_wheel

FROM python:alpine3.16
WORKDIR /opt/python-bot

# Install the wheel just generated.
COPY --from=build /opt/python-bot/dist/*.whl ./
RUN python3 install *.whl

# Prefix to use when issuing commands.
ENV BOT_PREFIX = "UNSET_PREFIX"

# Secret token for the bot.
ENV BOT_TOKEN = "UNSET_TOKEN"

# Comma separated list of user IDs that have ownership over the bot.
ENV BOT_OWNERS = "UNSET_OWNER_IDS SEPARATED_BY_SPACE"

ENV BOT_DATABASE_FILE_LOCATION = "/path/to/database.db"

ENV BOT_BLACKLIST_FILE_LOCATION = "/path/to/blacklist.json"

ENV BOT_CONFIG_FILE_LOCATION = "/path/to/config.json"

ENTRYPOINT ["python3", "-m", "dogbot"]
CMD ["--help"]
