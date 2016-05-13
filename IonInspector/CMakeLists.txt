# Copyright (C) 2010 Ion Torrent Systems, Inc. All Rights Reserved
cmake_minimum_required (VERSION 2.8.12)

project (ion-inspector)
set(PROJECT_DESCRIPTION "Ion Inspector")
enable_testing()

set(CPACK_DEBIAN_PACKAGE_DEPENDS "
    python,
    rabbitmq-server,
    celeryd
")