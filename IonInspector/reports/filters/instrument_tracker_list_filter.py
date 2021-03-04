import django_filters as filters

from reports.models import ValkyrieArchive


class InstrumentTrackerListFilter(filters.FilterSet):
    archive__is_baseline = filters.BooleanFilter(
        field_name="archive__is_baseline", label="Is Baseline?", lookup_expr="exact"
    )

    class Meta:
        model = ValkyrieArchive
        fields = {"run_name": ["icontains"], "archive__is_baseline": ["exact"]}
