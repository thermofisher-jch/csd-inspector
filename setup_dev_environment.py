#!/usr/bin/env python3

import subprocess
from pathlib import Path

# creating .local folders for logs and archives
local_dev_dirs = [".local/celery", ".local/media", ".local/logs", ".local/postgresql_log"]

for dir_name in local_dev_dirs:
    Path(dir_name).mkdir(mode=0o777, exist_ok=True)

subprocess.run(["dir", ".local"], shell=True)

# create docker volume for postgres
subprocess.run(["docker", "volume", "create", "postgresql-data"], shell=True)
subprocess.run(["docker", "volume", "ls"], shell=True)
