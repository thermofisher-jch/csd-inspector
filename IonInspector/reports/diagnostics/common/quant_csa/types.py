# This is a DataClass
class QuantDataModel:
    """
    Dataclass representing source data from a single purification batch loaded from a CSA.

    Instances of this model are usually produced by a QuantParser interpreting content of a
    Quant_summary.csv file, but nothing about its content depends on that assumption.  If used
    in a context where the are multiple purification batches in existence, any context required
    to associate each instance dataclass with its correct origin must be provided by semantics
    of that containing model (e.g. by named properties if the number of instances is fixed,
    or as the value in a dictionary keyed by batch identifier if variable).
    """

    def __init__(self, headers_table, barcodes_table, samples_table):
        self._headers_table = headers_table
        self._barcodes_table = barcodes_table
        self._samples_table = samples_table

    @property
    def header_table(self):
        return self._headers_table

    @property
    def barcodes_table(self):
        return self._barcodes_table

    @property
    def samples_table(self):
        return self._samples_table


class QuantFormatSpec:
    """
    Dataclass representing metadata specification about how to parse Quant_summary.csv

    QuantParserFactory creates a QuantParser by discovering correct content for an instance
    of this dataclass, given source Quant_summary.csv file's location and a parser for its ExpLog
    (see reports.diagnostics.common.explog.types.IExpLog), which is then used to configure
    constructed QuantParser instance before returning it to caller.
    """

    def __init__(
        self,
        first_row_count=-1,
        second_row_count=-1,
        samples_offset=-1,
        samples_row_count=-1,
        barcode_offset=-1,
        barcode_row_count=-1,
    ):
        self._first_row_count = first_row_count
        self._second_row_count = second_row_count
        self._samples_offset = samples_offset
        self._samples_row_count = samples_row_count
        self._barcode_offset = barcode_offset
        self._barcode_row_count = barcode_row_count

    @property
    def first_row_count(self):
        return self._first_row_count

    @property
    def second_row_count(self):
        return self._second_row_count

    @property
    def samples_offset(self):
        return self._samples_offset

    @property
    def samples_row_count(self):
        return self._samples_row_count

    @property
    def barcode_offset(self):
        return self._barcode_offset

    @property
    def barcode_row_count(self):
        return self._barcode_row_count
