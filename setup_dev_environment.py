#!/usr/bin/env python3

from pathlib import Path

# creating .local folders for logs and archives
local_dev_dirs = [
    ".local/celery",
    ".local/media",
    ".local/logs",
    ".local/postgresql_log",
]

for dir_name in local_dev_dirs:
    Path(dir_name).mkdir(mode=0o777, parents=True, exist_ok=True)
