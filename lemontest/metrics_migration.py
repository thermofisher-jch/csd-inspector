'''
Authorr: Anthony Rodriguez
'''
import logging
import transaction

from celery.task import task

from lemontest.models import DBSession
from lemontest.models import Archive
from lemontest.models import MetricsPGM
from lemontest.models import MetricsProton

from lemontest.upload import set_metrics_pgm
from lemontest.upload import set_metrics_proton

@task
def metrics_migration(archive_id):
    archive = DBSession.query(Archive).get(archive_id)

    if archive.archive_type == "PGM_Run":
        metrics_pgm = MetricsPGM()
        metrics_pgm.archive_id = archive_id
        DBSession.add(metrics_pgm)
        DBSession.flush()
        set_metrics_pgm.delay(metrics_pgm.id)

    elif archive.archive_type == "Proton":
        metrics_proton = MetricsProton()
        metrics_proton.archive_id = archive_id
        DBSession.add(metrics_proton)
        DBSession.flush()
        set_metrics_proton.delay(metrics_proton.id)

    elif archive.archive_type == "OT_Log":
        metrics_otlog = MetricsOTLog()
        metrics_otlog.archive_id = archive_id
        DBSession.add(metrics_otlog)
        DBSession.flush()
        set_metrics_otlog.delay(metrics_otlog.id)
    else:
        return

    transaction.commit()