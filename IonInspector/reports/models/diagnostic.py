import errno
import importlib
import json
import os
import shutil
# import traceback

from cached_property import cached_property
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django.utils import timezone

from reports.diagnostics.common.inspector_utils import (
    write_error_html,
    write_uncaught_error,
)
from reports.values import (
    CATEGORY_SEQUENCING,
    DIAGNOSTIC_STATUSES,
    UNEXECUTED,
    CATEGORY_CHOICES,
    EXECUTING,
    FAILED,
)

if not settings.configured:
    settings.configure()


class Diagnostic(models.Model):
    """A test to run against an archive"""

    class Meta:
        ordering = ["name"]
        app_label = "reports"

    # model attributes
    name = models.CharField(max_length=255, default="")
    status = models.CharField(
        max_length=255, choices=DIAGNOSTIC_STATUSES, default=UNEXECUTED
    )
    details = models.CharField(max_length=2048, default="")
    error = models.CharField(max_length=2048, default="")
    html = models.CharField(max_length=255, default="")
    priority = models.IntegerField(default=0)
    start_execute = models.DateTimeField(null=True)
    results = JSONField(null=True, default={})

    category = models.CharField(
        max_length=3, default=CATEGORY_SEQUENCING, choices=CATEGORY_CHOICES
    )

    # model relationships
    archive = models.ForeignKey(
        "Archive", related_name="diagnostics", on_delete=models.CASCADE
    )

    @cached_property
    def display_name(self):
        return self.name.replace("_", " ").title()

    @cached_property
    def diagnostic_root(self):
        """returns the root of the files used in the diagnostic"""
        test_folder = os.path.join(self.archive.archive_root, "test_results")
        results_folder = os.path.join(test_folder, self.name)
        if not os.path.exists(results_folder):
            # other workers may have already made the folder
            try:
                os.mkdir(results_folder)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        return results_folder

    @cached_property
    def readme(self):
        return os.path.exists(
            os.path.join(
                settings.SITE_ROOT,
                "IonInspector",
                "reports",
                "diagnostics",
                self.name,
                "README",
            )
        )

    def execute(self):
        """This will execute the this diagnostic"""

        try:
            # set the status
            self.status = EXECUTING
            self.start_execute = timezone.now()
            self.save()

            # execute the script
            diagnostic_module = importlib.import_module(
                "IonInspector.reports.diagnostics."
                + self.name.replace(" ", "_")
                + ".main"
            )
            if settings.DEBUG:
                reload(diagnostic_module)
            diagnostic_results = diagnostic_module.execute(
                self.archive.archive_root,
                self.diagnostic_root,
                self.archive.archive_type,
            )
            assert not isinstance(
                diagnostic_results, type(None)
            ), "Diagnostic is broken (Returned None)"
            self.status, self.priority, self.details = diagnostic_results

            html_path = os.path.join(self.diagnostic_root, "results.html")
            if os.path.exists(html_path):
                self.html = os.path.basename(html_path)

            json_path = os.path.join(self.diagnostic_root, "main.json")
            if os.path.exists(json_path):
                with open(json_path) as fp:
                    self.results = json.load(fp)

        except Exception as exc:
            self.details = "Failed. <a href="+self.archive.archive_root.replace("/var/lib/inspector","")+"/test_results/"+self.name.replace(" ", "_")+"/results.html> Error Link </a> " #+str(exc)
            #self.details = self.diagnostic_root #+"/results.html  Error Link" #</a> bb " #+str(exc)
            # traceback.print_exc()
            # trace = traceback.format_exc()
            # write_uncaught_error(self.diagnostic_root, trace)
            # if len(trace) > 500:
            #      # Trim to fit by cutting out the middle part of stack trace--most value is at the head and tail...
            #     trace = trace[:120] + "\n...\n" + trace[-375:]
            # self.details = "<pre>" + trace + "</pre>"
            # record the exception in the details and rely on the finally statement to call save
            write_error_html(self.diagnostic_root)
            self.status = FAILED

        # constrain the length of the details to 512
        self.details = self.details[:512]
        self.save()


# TODO: Receivers should not be imported from a model file as this can
#       lead to them registering for the same events multiple times.


@receiver(pre_delete, sender=Diagnostic, dispatch_uid="delete_diagnostic")
def on_diagnostic_delete(sender, instance, **kwargs):
    """Triggered when the diagnostic are deleted"""
    if os.path.exists(instance.diagnostic_root):
        shutil.rmtree(instance.diagnostic_root)
