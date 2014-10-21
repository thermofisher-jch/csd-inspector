'''
Authorr: Anthony Rodriguez
'''
import logging
import transaction

from celery.task import task

from lemontest.models import DBSession
from lemontest.models import Archive
from lemontest.models import MetricsPGM, MetricsProton, MetricsOTLog

from lemontest.upload import set_metrics_pgm
from lemontest.upload import set_metrics_proton, set_metrics_otlog

@task
def metrics_migration(archive_id):
    archive = DBSession.query(Archive).get(archive_id)


    if archive.archive_type == "PGM_Run":
        if DBSession.query(MetricsPGM).filter_by(archive_id=archive_id).count():
            return
        metrics_pgm = MetricsPGM()
        metrics_pgm.archive_id = archive_id
        DBSession.add(metrics_pgm)
        DBSession.flush()
        set_metrics_pgm.delay(metrics_pgm.id)

    elif archive.archive_type == "Proton":
        if DBSession.query(MetricsProton).filter_by(archive_id=archive_id).count():
            return
        metrics_proton = MetricsProton()
        metrics_proton.archive_id = archive_id
        DBSession.add(metrics_proton)
        DBSession.flush()
        set_metrics_proton.delay(metrics_proton.id)

    elif archive.archive_type == "OT_Log":
        if DBSession.query(MetricsOTLog).filter_by(archive_id=archive_id).count():
            return
        metrics_otlog = MetricsOTLog()
        metrics_otlog.archive_id = archive_id
        DBSession.add(metrics_otlog)
        DBSession.flush()
        set_metrics_otlog.delay(metrics_otlog.id)
    else:
        return

    transaction.commit()