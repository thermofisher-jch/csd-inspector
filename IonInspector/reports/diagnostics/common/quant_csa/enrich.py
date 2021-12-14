from reports.diagnostics.common.reporting import IModelEnricher


class QuantSummaryEnricher(IModelEnricher):
    def __init__(self):
        IModelEnricher.__init__(self)

    def enrich_model(self, data_model):
        header_data = reduce(
            lambda sum, next: sum.join(next),
            (quant_summary.quant_header_record for quant_summary in data_model),
        )
        header_data = header_data.to_html(
            bold_rows=True,
            classes="header-table table table-bordered table-sm",
            header=True,
            justify="left",
            col_space=400,
            index_names=False,
        )
        quant_data = [
            {
                "label": quant_summary.batch_label,
                "table": quant_summary.quant_samples_table.to_html(
                    justify="center",
                    bold_rows=False,
                    header=True,
                    index=False,
                    classes="quant-table card-body table table-bordered table-striped",
                ),
                "columns": quant_summary.quant_samples_table.columns.names,
            }
            for quant_summary in data_model
        ]
        return {"header_data": header_data, "quant_data": quant_data}


class ConsumableLotsSummaryEnricher(IModelEnricher):
    def __init__(self):
        IModelEnricher.__init__(self)

    def enrich_model(self, data_models):
        return {
            "consumable_data": [
                {
                    "label": quant_summary.batch_label,
                    "table": quant_summary.quant_barcode_table.to_html(
                        bold_rows=True,
                        classes="header-table table table-striped table-bordered table-sm",
                        header=True,
                        columns=["Plate Name", "Barcode", "expiryDate", "Lot Number"],
                        justify="left",
                        col_space=400,
                        index_names=False,
                    ),
                }
                for quant_summary in data_models
            ],
        }
