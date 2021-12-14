import functools32
import pandas as pd

from reports.diagnostics.common.quant_csa.types import QuantFormatSpec

pd.set_option("max_colwidth", 256)


class QuantParser:
    """
    Follow specification given by QuantParserSpec to parse Quant_summary.csv.
    """

    def __init__(self, batch_label, quant_summary_file_path, feature_layout):
        self._batch_label = batch_label
        self._quant_summary_file_path = quant_summary_file_path
        self._first_row_count = feature_layout.first_row_count
        self._second_row_count = feature_layout.second_row_count
        self._samples_offset = feature_layout.samples_offset
        self._barcode_offset = feature_layout.barcode_offset
        self._barcode_row_count = feature_layout.barcode_row_count

    @property
    def batch_label(self):
        return self._batch_label

    @property
    def file_path(self):
        return self._quant_summary_file_path

    @property
    @functools32.lru_cache(maxsize=1)
    def quant_samples_table(self):
        return pd.read_csv(
            self._quant_summary_file_path,
            engine="c",
            skiprows=self._samples_offset,
            skipinitialspace=True,
            header=0,
        )

    @property
    @functools32.lru_cache(maxsize=1)
    def quant_barcode_table(self):
        barcode_table = None
        if self._barcode_offset > -1:
            barcode_table = pd.read_csv(
                self._quant_summary_file_path,
                engine="c",
                skiprows=self._barcode_offset,
                skipinitialspace=True,
                nrows=self._barcode_row_count,
                header=0,
            )
        return barcode_table

    @property
    @functools32.lru_cache(maxsize=1)
    def quant_header_record(self):
        header_record = pd.read_csv(
            self._quant_summary_file_path,
            engine="c",
            nrows=self._first_row_count,
            header=None,
            skipinitialspace=True,
            names=["key", self._batch_label],
            index_col=0,
            skip_blank_lines=True,
            encoding="utf-8",
        )
        if self._second_row_count > 0:
            second_header = pd.read_csv(
                self._quant_summary_file_path,
                engine="c",
                nrows=self._second_row_count,
                header=None,
                skipinitialspace=True,
                names=["key", self._batch_label],
                index_col=0,
                skiprows=self._first_row_count + 1,
                skip_blank_lines=True,
                encoding="utf-8",
            )
            header_record = pd.concat([header_record, second_header])
        return header_record

    @property
    @functools32.lru_cache(maxsize=1)
    def quant_header_table(self):
        header_table = self.quant_header_record.reset_index()
        header_table["id"] = "quant"
        return header_table.pivot(index="id", columns="key", values="value")

    @property
    @functools32.lru_cache(maxsize=1)
    def run_execution_time(self):
        return pd.to_datetime(
            self.quant_header_table.loc["quant", "Run Execution Time"]
        )


class QuantParserFactory:
    """
    Encapsulates logic that discovers how to parse a Quant_summary.csv file, given its location,
    and returns a QuantParser configured to follow discovered QuantFormatSpec.
    """

    def __init__(self):
        pass

    def create_parser(self, instance_name, quant_summary_file_path):
        row_counter = 0
        null_row_indices = list()
        with open(quant_summary_file_path, "rb") as source:
            content = source.readline(1024)
            while content != "":
                if content == "\n":
                    null_row_indices.append(row_counter)
                row_counter += 1
                content = source.readline(1024)
        block_count = len(null_row_indices) + 1
        if block_count == 3:
            format_spec = QuantFormatSpec(
                first_row_count=null_row_indices[0],
                second_row_count=null_row_indices[1] - null_row_indices[0] - 1,
                samples_offset=null_row_indices[1] + 1,
                samples_row_count=row_counter - null_row_indices[1] - 2,
                barcode_offset=-1,
                barcode_row_count=1,
            )
        elif block_count == 4:
            format_spec = QuantFormatSpec(
                first_row_count=null_row_indices[0],
                second_row_count=null_row_indices[1] - null_row_indices[0] - 1,
                samples_offset=null_row_indices[2] + 1,
                samples_row_count=row_counter - null_row_indices[2] - 2,
                barcode_offset=null_row_indices[1] + 1,
                barcode_row_count=null_row_indices[2] - null_row_indices[1] - 2,
            )
        else:
            raise ValueError(
                "Quant summary must have 3 or 4 sections, but <"
                + str(block_count)
                + "> were found with boundaries at lines <"
                + str(null_row_indices)
                + ">"
            )
        return QuantParser(instance_name, quant_summary_file_path, format_spec)
