from IonInspector import settings
from os.path import abspath, join

CATEGORY_SEQUENCING = "SEQ"
CATEGORY_SAMPLE_PREP = "PRE"
CATEGORY_LIBRARY_PREP = "LIB"
CATEGORY_CHOICES = (
    (CATEGORY_SEQUENCING, "SEQUENCING"),
    (CATEGORY_SAMPLE_PREP, "SAMPLE_PREP"),
    (CATEGORY_LIBRARY_PREP, "LIBRARY_PREP"),
)

# define constants
PGM_RUN = "PGM_Run"
PROTON = "Proton"
PURE = "Purification"
S5 = "S5"
OT_LOG = "OT_Log"
ION_CHEF = "Ion_Chef"
VALK = "Valkyrie"
DIAG = "Diagnostic"
UNKNOWN_PLATFORM = "Unknown Platform"

# Well known explog keys and values
PURIFICATION_BATCH_ID = "Purification Batch ID"
EXTRACTION_KIT = "ExtractionKit"
PROTOCOL_NAME = "ProtocolName"

# define a list of archive types
ARCHIVE_TYPES = (
    (PGM_RUN, "PGM"),
    (PROTON, "PROTON"),
    (PURE, "Purification"),
    (S5, "S5"),
    (VALK, "Genexus"),
    (DIAG, "Diagnostic"),
    (OT_LOG, "OT"),
    (ION_CHEF, "CHEF"),
)

CHIP_TYPES = (
    ("GX5","GX5"),
    ("GX7","GX7"),
    ("GX9","GX9"),
    ("530","530"),
    ("540","540"),
    ("541","541"),
    ("550","550"),
    ("560","560"),
    )

# Diagnostic states
UNEXECUTED = "Unexecuted"
EXECUTING = "Executing"
ALERT = "Alert"
INFO = "Info"
WARNING = "Warning"
OK = "OK"
NA = "NA"
FAILED = "Failed"

DIAGNOSTIC_STATUSES = (
    ("U", UNEXECUTED),
    ("E", EXECUTING),
    ("A", ALERT),
    ("I", INFO),
    ("W", WARNING),
    ("O", OK),
    ("N", NA),
    ("F", FAILED),
)

DIAGNOSTICS_SCRIPT_DIR = "/opt/inspector/IonInspector/reports/diagnostics"

# define constants
UNKNOWN = "Unknown"

# define a list of archive types
UPLOAD_TYPES = (
    (UNKNOWN, "UNKNOWN"),
    (PGM_RUN, "PGM"),
    (PROTON, "PROTON"),
    (PURE, "Purification"),
    (S5, "S5"),
    (VALK, "Genexus"),
    (DIAG, "Diagnostic"),
    (OT_LOG, "OT"),
    (ION_CHEF, "CHEF"),
)

TEST_RUN_TYPES = (
    (PGM_RUN, "PGM"),
    (PROTON, "PROTON"),
    (PURE, "Purification"),
    (S5, "S5"),
    (VALK, "Genexus"),
    (DIAG, "Diagnostic"),
    (OT_LOG, "OT"),
    (ION_CHEF, "CHEF"),
)

SYMBOLIC_UNK = u"\u2047"
SYMBOLIC_YES = u"\u2714"
SYMBOLIC_NO = u"\u2718"
TRI_STATE_SYMBOL_SELECT = (
    (b"K", SYMBOLIC_UNK),
    (b"T", SYMBOLIC_YES),
    (b"F", SYMBOLIC_NO),
)
TRI_STATE_SYMBOL_DICT = {"K": SYMBOLIC_UNK, "T": SYMBOLIC_YES, "F": SYMBOLIC_NO}

VERBAL_UNK = "Unknown"
VERBAL_YES = "Known Good"
VERBAL_NO = "Known Issue"
TRI_STATE_VERBAL = ((b"K", VERBAL_UNK), (b"T", VERBAL_YES), (b"F", VERBAL_NO))


class LaneMeta:
    def __init__(self, index, value_callback):
        self._index = index
        self._value_callback = value_callback
        self._bit_mask = 1 << (index - 1)

    @property
    def index(self):
        return self._index

    @property
    def bit_mask(self):
        return self._bit_mask

    def value(self, archive):
        return self._value_callback(archive)


NGINX_UPLOAD_MAP = {
    "doc_file.md5": "doc_file_md5",
    "doc_file.sha1": "doc_file_sha1",
    "doc_file.number": "doc_file_number",
    "doc_file.size": "doc_file_size",
    "doc_file.crc32": "doc_file_crc32",
    "doc_file.path_saved": "doc_file_path_saved",
    "doc_file.source_name": "doc_file_source_name",
    "doc_file.content_type": "doc_file_content_type",
}
LANE_META_OBJECTS = [
    LaneMeta(1, lambda x: x.lane1_assay_type),
    LaneMeta(2, lambda x: x.lane2_assay_type),
    LaneMeta(3, lambda x: x.lane3_assay_type),
    LaneMeta(4, lambda x: x.lane4_assay_type),
]

# Well-known path elements used to assemble canonical path locations in CSA archives and
# locate the root of a namespace reserved for in-container diagnostic state.
DIAGNOSTICS_ROOT_ROLE = "Diagnostics Root Namespace"
DIAGNOSTICS_NAMESPACE_ROOT = "test_results"
GENEXUS_INSTRUMENT_TRACKER_DIAGNOSTIC_NAME = "GenexusInstrumentTracker"
GENEXUS_LANE_ACTIVITY_DIAGNOSTIC_NAME = "Genexus_Lane_Activity"
BEAD_DENSITY_FILE_NAME = "Bead_density_1000.png"

WELL_KNOWN_ARCHIVE = ".inner_archive.tgz"
AMBIGUOUS_MARKER = "AmBiguOus.zzz"
PLANNED_RUN_AUDIT_TRAIL_PDF = "PlannedRun-AuditTrail.pdf"
RUN_REPORT_PDF = "report.pdf"
FULL_REPORT_PDF = "full_report.pdf"
NOT_RUN_REPORT_LINK_TARGETS = {
    PLANNED_RUN_AUDIT_TRAIL_PDF,
    RUN_REPORT_PDF,
    FULL_REPORT_PDF,
}

NO_BEAD_IMAGE_URL = "static/img/no-bead-density-found.png"
NO_BEAD_IMAGE_FILE = join(abspath(settings.BASE_DIR), NO_BEAD_IMAGE_URL)
