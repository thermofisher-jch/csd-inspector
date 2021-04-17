import django_filters as filters

from reports.models import ValkyrieArchive
from reports.values import TRI_STATE_SYMBOL_SELECT


class InstrumentTrackerListFilter(filters.FilterSet):
    is_known_good = filters.MultipleChoiceFilter(
        field_name="is_known_good",
        choices=TRI_STATE_SYMBOL_SELECT,
        label="Known Good Run?",
        lookup_expr="in",
    )

    class Meta:
        model = ValkyrieArchive
        fields = []
