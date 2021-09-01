import pandas as pd

pd.set_option("max_colwidth", 256)


class QuantFeatureEvaluator():
    """
    Encapsulates logic that discovers how to parse a Quant_summary.csv file
    """
    def __init__(self, quant_summary_file_path):
        self._quant_summary_file_path = quant_summary_file_path
        self._feature_layout = None

    def find_layout_features(self):
        if self._feature_layout is None:
            practice_read = pd.read_csv(self._quant_summary_file_path, engine="c",
                                        error_bad_lines=False, skipinitialspace=True,
                                        verbose=True, header=None, names=["key", "value"],
                                        skip_blank_lines=False)
            null_row_indices = pd.Series(range(len(practice_read))) \
                                   .where(pd.isnull(practice_read['key']), -1) \
                                   .unique()[1:]
            block_count = len(null_row_indices)
            if block_count == 2:
                _first_row_count = null_row_indices[0]
                _second_row_count = null_row_indices[1] - null_row_indices[0] - 1
                _samples_offset = null_row_indices[1] + 1
                _samples_row_count = len(practice_read) - null_row_indices[1] - 2
                _barcode_offset = -1
                _barcode_row_count = 1
            elif block_count == 3:
                _first_row_count = null_row_indices[0]
                _second_row_count = null_row_indices[1] - null_row_indices[0] - 1
                _samples_offset = null_row_indices[2] + 1
                _samples_row_count = len(practice_read) - null_row_indices[2] - 2
                _barcode_offset = null_row_indices[1] + 1
                _barcode_row_count = null_row_indices[2] - null_row_indices[1] - 2
            else:
                raise ValueError(
                    "Unexpected header block count of <" + str(block_count) + "> at <" +
                    str(null_row_indices) + ">"
                )
            practice_read = pd.read_csv(
                self._quant_summary_file_path, engine="c", error_bad_lines=False,
                skiprows=_samples_offset, skipinitialspace=True, header=0,
                nrows=_samples_row_count
            )
            column_count = len(practice_read.columns)
            if column_count == 5:
                raise ValueError(
                    "Error! <5> <" + str(_samples_offset) +
                    "> <" + str(_samples_row_count) + ">"
                )
            elif column_count != 6:
                raise ValueError(
                    "Unexpected post-headers block column count of <" + str(column_count) + ">"
                )

            if _barcode_offset > -1 and _barcode_row_count > 0:
                practice_read = pd.read_csv(
                    self._quant_summary_file_path, engine="c", error_bad_lines=False,
                    skiprows=_barcode_offset, skipinitialspace=True, header=0,
                    nrows=_barcode_row_count
                )
                column_count = len(practice_read.columns)
                if column_count == 6:
                    raise ValueError(
                        "Error! <5> <" + str(_samples_offset) +
                        "> <" + str(_samples_row_count) + ">"
                    )
                elif column_count != 5:
                    raise ValueError(
                        "Unexpected post-headers block column count of <" + str(column_count) + ">"
                    )

            self._feature_layout = QuantFeatureLayout(
                _first_row_count, _samples_offset, _samples_row_count,
                second_row_count=_second_row_count,
                barcode_offset=_barcode_offset, barcode_row_count=_barcode_row_count,
            )
        return self._feature_layout


# This is a Dataclass
class QuantFeatureLayout():
    """
    Serializable/Restorable description about how to parse Quant_summary.csv
    """
    def __init__(
        self, first_row_count, samples_offset, samples_row_count,
        second_row_count=-1, barcode_offset=-1, barcode_row_count=-1
    ):
        self._first_row_count = first_row_count
        self._second_row_count = second_row_count
        self._samples_offset = samples_offset
        self._samples_row_count = samples_row_count
        self._barcode_offset = barcode_offset
        self._barcode_row_count = barcode_row_count


class QuantDataSource():
    """
    Follow specification given by QuantFeatureLayout to parse Quant_summary.csv.
    """
    def __init__(self, quant_summary_file_path, feature_layout):
        self._quant_summary_file_path = quant_summary_file_path
        self._first_row_count = feature_layout._first_row_count
        self._second_row_count = feature_layout._second_row_count
        self._samples_offset = feature_layout._samples_offset
        self._barcode_offset = feature_layout._barcode_offset
        self._barcode_row_count = feature_layout._barcode_row_count
        self._header_record = None
        self._header_table = None
        self._barcode_table = None
        self._samples_table = None

    @property
    def quant_header_record(self):
        if self._header_record is None:
            self._header_record = pd.read_csv(
                self._quant_summary_file_path, engine="c", nrows=self._first_row_count,
                header=None, skipinitialspace=True, names=["key", "value"], index_col=0,
                skip_blank_lines=True, encoding="utf-8")
            if self._second_row_count > 0:
                second_header = pd.read_csv(
                    self._quant_summary_file_path, engine="c", nrows=self._second_row_count,
                    header=None, skipinitialspace=True, names=["key", "value"], index_col=0,
                    skiprows=self._first_row_count + 1, skip_blank_lines=True, encoding="utf-8")
                self._header_record = pd.concat([self._header_record, second_header])
        return self._header_record;

    @property
    def quant_header_table(self):
        if self._header_table is None:
            header_table = self.quant_header_record.reset_index()
            header_table['id'] = 'quant'
            self._header_table = header_table.pivot(index='id', columns='key', values='value')
        return self._header_table

    @property
    def run_execution_time(self):
        return pd.to_datetime(
            self.quant_header_table.loc['quant','Run Execution Time']
        )

    @property
    def quant_samples_table(self):
        if self._samples_table is None:
            self._samples_table = pd.read_csv(
                self._quant_summary_file_path, engine="c", skiprows=self._samples_offset,
                skipinitialspace=True, header=0
            )
        return self._samples_table

    @property
    def quant_barcode_table(self):
        if self._barcode_table is None and self._barcode_offset > -1:
            self._barcode_table = pd.read_csv(
                self._quant_summary_file_path, engine="c", skiprows=self._barcode_offset,
                skipinitialspace=True, nrows=self._barcode_row_count, header=0
            )
        return self._barcode_table


def inject_quant_data_source(files_config):
    quant_file_path = files_config['Quant_summary']
    quant_file_evaluator = QuantFeatureEvaluator(quant_file_path)
    file_features = quant_file_evaluator.find_layout_features()
    return QuantDataSource(quant_file_path, file_features)
