import simple_parsing

from dogbot.config import Config, source_and_merge_base_config
from dogbot.main import main


def console_entry() -> None:
    """
    Entrypoint for the bot. Parses arguments and finalises config before running the bot.
    """
    parser = simple_parsing.ArgumentParser()
    parser.add_arguments(Config, dest="config")
    args = parser.parse_args()

    # Merge the base config in, if necessary.
    if args.config.merge_with_config_file:
        standardised_config = source_and_merge_base_config(args.config)
    else:
        standardised_config = args.config
    main(standardised_config)


if __name__ == "__main__":
    console_entry()
