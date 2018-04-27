from celeryconfig import celery_app
from models import Diagnostic


@celery_app.task
def execute_diagnostic(diagnostic_id):
    Diagnostic.objects.get(id=diagnostic_id).execute()
