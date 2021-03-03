CATEGORY_SEQUENCING = "SEQ"
CATEGORY_SAMPLE_PREP = "PRE"
CATEGORY_CHOICES = (
    (CATEGORY_SEQUENCING, "SEQUENCING"),
    (CATEGORY_SAMPLE_PREP, "SAMPLE_PREP"),
)

# define constants
PGM_RUN = "PGM_Run"
PROTON = "Proton"
S5 = "S5"
OT_LOG = "OT_Log"
ION_CHEF = "Ion_Chef"
VALK = "Valkyrie"
UNKNOWN_PLATFORM = "Unknown Platform"

# define a list of archive types
ARCHIVE_TYPES = (
    (PGM_RUN, "PGM"),
    (PROTON, "PROTON"),
    (S5, "S5"),
    (VALK, "Genexus"),
    (OT_LOG, "OT"),
    (ION_CHEF, "CHEF"),
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
    (S5, "S5"),
    (VALK, "Genexus"),
    (OT_LOG, "OT"),
    (ION_CHEF, "CHEF"),
)

TEST_RUN_TYPES = (
    (PGM_RUN, "PGM"),
    (PROTON, "PROTON"),
    (S5, "S5"),
    (VALK, "Genexus"),
    (OT_LOG, "OT"),
    (ION_CHEF, "CHEF"),
)


SAFE_SELF_TEMPLATE = "<a href='%s' class='no-underline' target='_blank'>%s</a>"
