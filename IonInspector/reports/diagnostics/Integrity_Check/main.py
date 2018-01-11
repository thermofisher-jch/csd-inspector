#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import magic
import os
import traceback
import xml.etree.ElementTree
import xml.parsers.expat

from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        EXTENSION_MIME_TYPES = {
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".zip": "application/zip",
        }

        if archive_type == "Ion_Chef":
            # Check that the file type matches the extension
            compressed_archive_path = None
            # We need to guess at the path to the uncompressed archives
            for filename in os.listdir(archive_path):
                if filename.endswith(".tar") or filename.endswith(".tar.gz") or filename.endswith(".zip"):
                    compressed_archive_path = os.path.join(archive_path, filename)
            if compressed_archive_path:
                _, file_extension = os.path.splitext(compressed_archive_path)
                magic_parser = magic.Magic(mime=True, uncompress=False)
                file_mime_type = magic_parser.from_file(compressed_archive_path)

                if file_extension not in EXTENSION_MIME_TYPES.keys():
                    return print_failed("Unknown archive file extension: %s" % file_extension)

                if file_mime_type not in EXTENSION_MIME_TYPES.values():
                    return print_failed("Unknown archive file type: %s" % file_mime_type)

                if EXTENSION_MIME_TYPES[file_extension] != file_mime_type:
                    return print_failed("Archive extension '%s' does not match file type '%s'" %
                                 (os.path.basename(compressed_archive_path), file_mime_type))

            else:
                return print_failed("Cannot find compressed archive!")

            # Check the chef run log xml for validity
            xml_path = None
            run_log_directory = os.path.join(archive_path, 'var', 'log', 'IonChef', 'RunLog')
            for run_log in os.listdir(run_log_directory):
                if run_log.endswith('.xml'):
                    xml_path = os.path.join(run_log_directory, run_log)
                    break

            if not xml_path:
                return print_failed("Could not find run log!")
            try:
                xml.etree.ElementTree.parse(xml_path)
            except Exception as e:
                with open(os.path.join(output_path, "results.html"), 'w') as output_file:
                    traceback.print_exc(file=output_file)
                if getattr(e, "code", None) == 4:
                    return print_failed("Run log contains invalid characters. Possibly a known issue with IC before v5.4.")
                else:
                    return print_failed("Invalid run log xml: %s" % str(e))

            return print_ok("")
        else:
            return print_na("")
    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)
