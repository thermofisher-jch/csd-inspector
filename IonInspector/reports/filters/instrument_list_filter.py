import django_filters as filters

from reports.models import Instrument


class InstrumentListFilter(filters.FilterSet):
    class Meta:
        model = Instrument
        fields = {
            "serial_number": ["icontains"],
            "site": ["icontains"],
            "instrument_name": ["icontains"],
        }
