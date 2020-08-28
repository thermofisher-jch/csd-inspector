#!/usr/bin/env python3
# port to fabric2

from invoke import Collection
import tasks
import prod

namespace = Collection()

namespace.add_collection(prod)
namespace.add_collection(tasks, "local")
