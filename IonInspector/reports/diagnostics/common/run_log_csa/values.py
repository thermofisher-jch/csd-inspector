import numpy as np
from django.utils.safestring import SafeString

from .types import LibPrepColumnSpec, LibPrepEnrichmentMeta, LibPrepMetricSpec

NAN = float("nan")


def to_float(value):
    value_type = type(value)
    if value_type == str:
        if value.lower() == "nan":
            return NAN
    elif np.isnan(value):
        return NAN
    return float(value)


FREQUENCY_METRIC = "fan"
TEMPERATURE_METRIC = "temp"
TIME_COLUMN_KEY = "time"

DEFAULT_GAP_TOLERANCE = 45
FLOAT_DECODER = "reports.diagnostics.common.run_log_csa.values:to_float"
TIME_ELAPSED_DISPLAY_LABEL = ("Time Elapsed (seconds)",)

"""
Parser metadata describes the mechanics of parsing a Purification run log file
"""
COLUMN_PARSE_CONFIG = {
    FREQUENCY_METRIC: [
        LibPrepColumnSpec("SystemFanTach", "System Fan", FLOAT_DECODER),
        LibPrepColumnSpec("CoolingFan1", "Cooling Fan 1", FLOAT_DECODER),
        LibPrepColumnSpec("CoolingFan2", "Cooling Fan 2", FLOAT_DECODER),
        LibPrepColumnSpec("CoolingPumpTach", "Cooling Pump", FLOAT_DECODER),
    ],
    TEMPERATURE_METRIC: [
        LibPrepColumnSpec("Ambient1", "Ambient 1", FLOAT_DECODER),
        LibPrepColumnSpec("Ambient1.1", "Ambient 2", FLOAT_DECODER),
        LibPrepColumnSpec("DeckTemp", "Deck", FLOAT_DECODER),
        LibPrepColumnSpec("LiquidCooling", "Liquid Cooling", FLOAT_DECODER),
        LibPrepColumnSpec("24WellPlate1", "24-Well Plate 1", FLOAT_DECODER),
        LibPrepColumnSpec(
            "24WellPlate1HeatSink", "24-Well Plate 1 Heat-Sink", FLOAT_DECODER
        ),
        LibPrepColumnSpec("24WellPlate2", "24-Well Plate 2", FLOAT_DECODER),
        LibPrepColumnSpec(
            "24WellPlate2HeatSink", "24-Well Plate 2 Heat-Sink", FLOAT_DECODER
        ),
        LibPrepColumnSpec("96WellPlate1", "96-Well Plate 1", FLOAT_DECODER),
        LibPrepColumnSpec(
            "96WellPlate1HeatSink", "96-Well Plate 1 Heat-Sink", FLOAT_DECODER
        ),
        LibPrepColumnSpec("96WellPlate2", "96-Well Plate 2", FLOAT_DECODER),
        LibPrepColumnSpec(
            "96WellPlate2HeatSink", "96-Well Plate 2 Heat-Sink", FLOAT_DECODER
        ),
        LibPrepColumnSpec("QuantConsumable", "Quant Consumable", FLOAT_DECODER),
        LibPrepColumnSpec(
            "QuantConsumableHeatSink", "Quant Consumable Heat-Sink", FLOAT_DECODER
        ),
        LibPrepColumnSpec("OutputPlate", "Output Plate", FLOAT_DECODER),
        LibPrepColumnSpec(
            "outputPlateHeatsink", "Output Plate Heat-Sink", FLOAT_DECODER
        ),
        LibPrepColumnSpec("ArchivePlate", "Archive Plate", FLOAT_DECODER),
        LibPrepColumnSpec(
            "ArchivePlateHeatSink", "Archive Plate Heat-Sink", FLOAT_DECODER
        ),
    ],
}

"""
Enrichment data describes how to visualize the parsed log data in a report
"""
RUN_REPORT_ENRICHMENT_META = LibPrepEnrichmentMeta(
    TIME_ELAPSED_DISPLAY_LABEL,
    {
        TEMPERATURE_METRIC: LibPrepMetricSpec(
            TEMPERATURE_METRIC,
            SafeString("Temperature (&deg;C)"),
            640,
            [
                "rgb(178,152,106)",
                "rgb(209,147,232)",
                "rgb(230,210,40)",
                "rgb(109,200,196)",
                "rgb(159,233,65)",
                "rgb(200,69,232)",
                "rgb(88,227,157)",
                "rgb(209,242,88)",
                "rgb(36,213,110)",
                "rgb(205,162,227)",
                "rgb(79,136,240)",
                "rgb(52,167,78)",
                "rgb(208,150,69)",
                "rgb(47,152,194)",
                "rgb(213,59,179)",
                "rgb(176,199,102)",
                "rgb(248,23,124)",
                "rgb(124,138,216)",
            ],
        ),
        FREQUENCY_METRIC: LibPrepMetricSpec(
            FREQUENCY_METRIC,
            "Fan (rpm) and Flow (spm) Rates",
            280,
            [
                "rgb(220,68,185)",
                "rgb(57,146,151)",
                "rgb(31,199,104)",
                "rgb(100,167,236)",
            ],
        ),
    },
)
