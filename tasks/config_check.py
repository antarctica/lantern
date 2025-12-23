from pprint import pprint

from lantern.config import Config, ConfigurationError


def main() -> None:
    """Entrypoint."""
    config = Config()
    try:
        config.validate()
        print("Configuration valid.")
        pprint(config.dumps_safe())
    except ConfigurationError as e:
        print("Configuration invalid:")
        print(e)


if __name__ == "__main__":
    main()
