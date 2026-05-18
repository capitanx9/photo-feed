#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
