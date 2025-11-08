"""
HOW TO USE:

In compose file add:

```
environment:
    LOGFILE_ELEMENT_LOGFILE_PATH: /data/log/weather_updates_
```
"""

import logging
import os
import time
from pathlib import Path

from nicegui import ui

LOGFILE_ELEMENT_LOGFILE_PATH = os.getenv(
    "LOGFILE_ELEMENT_LOGFILE_PATH", "./src/logfile_element/test"
)


class LogfileElement:
    def __init__(
        self, ui_log: ui.log, path_and_file_prefix: Path | str, interval: float = 0.1
    ):
        """Provide a path that ends with the prefix of the logfile we are looking for.

        Example:
            for `/data/log/weather_updates_20231105T165847.log` you should provide `/data/log/weather_updates_` to path_and_file_prefix to find the most recent log

        """

        self.path_and_file_prefix = Path(path_and_file_prefix)
        self.ui_log = ui_log

        found_path = self.find_file()
        self.last_mtime: float = found_path.stat().st_mtime

        self.update_ui_log(found_path)

        ui.timer(interval, self.watch_tick)
        logging.info(f"Watching {found_path}...")

    def update_ui_log(self, found_path: Path):
        self.ui_log.clear()

        with open(found_path, "r") as f:
            lines = f.readlines()
            self.ui_log.push("\n".join(lines))

    def watch_tick(self):
        try:
            found_path = self.find_file()

            current_mtime = found_path.stat().st_mtime
            if current_mtime != self.last_mtime:
                logging.debug(f"File changed at {time.ctime(current_mtime)}")
                self.last_mtime = current_mtime

                self.update_ui_log(found_path)

        except FileNotFoundError:
            logging.debug("File was deleted!")
            return

    def find_file(self) -> Path:
        directory = self.path_and_file_prefix.parent
        filename_prefix = self.path_and_file_prefix.name

        found_path = find_file_with_prefix(directory, filename_prefix)
        if not found_path:
            logging.warning(f"Logfile not found: {self.path_and_file_prefix}")

            raise FileNotFoundError

        return found_path


def find_file_with_prefix(directory: Path, prefix: str) -> Path | None:
    """
    Search for the most recent file in `directory` that starts with `prefix`.
    Returns the full path if found, otherwise None.
    """
    matching_files = [
        file_path
        for file_path in directory.iterdir()
        if file_path.is_file() and file_path.name.startswith(prefix)
    ]

    if not matching_files:
        return None

    # Return the file with the most recent modification time
    return max(matching_files, key=lambda p: p.stat().st_mtime)


def main():
    ui_log_element = ui.log(max_lines=500)
    if not LOGFILE_ELEMENT_LOGFILE_PATH:
        logging.error("No log file specified")
        return

    LogfileElement(ui_log_element, LOGFILE_ELEMENT_LOGFILE_PATH)
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
