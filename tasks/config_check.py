from pprint import pprint

from tasks._config import ExtraConfig

from lantern.config import ConfigurationError


def main() -> None:
    """Entrypoint."""
    config = ExtraConfig()
    try:
        config.validate()
        print("Configuration valid.")
        print("\nApp config:")
        pprint(config.dumps_safe())
        print("\nTasks extra config:")
        pprint(config.dumps_extra())
    except ConfigurationError as e:
        print("Configuration invalid:")
        print(e)


if __name__ == "__main__":
    main()
