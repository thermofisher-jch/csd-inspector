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
        if not archive.metrics_pgm:
            metrics_pgm = MetricsPGM()
            metrics_pgm.archive_id = archive.id
            DBSession.add(metrics_pgm)
            DBSession.flush()
            temp = metrics_pgm.id
            transaction.commit()
            set_metrics_pgm.delay(temp)
    elif archive.archive_type == "Proton":
        if not archive.metrics_proton:
            metrics_proton = MetricsProton()
            metrics_proton.archive_id = archive.id
            DBSession.add(metrics_proton)
            DBSession.flush()
            temp = metrics_proton.id
            transaction.commit()
            set_metrics_proton.delay(temp)
