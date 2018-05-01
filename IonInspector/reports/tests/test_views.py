from django.test import Client
from django.test import TestCase

from reports.models import Archive


class SingleUploadTestCase(TestCase):
    def test_upload_archive(self):
        c = Client()
        with open("/opt/inspector/.local/test_archives/ot.log") as fp:
            response = c.post("/upload/", {
                "name": "Alex",
                "site_name": "Michigan",
                "archive_identifier": "Test Archive",
                "taser_ticket_number": "444",
                "upload_another": "no",
                "doc_file": fp
            })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response["Location"], "/report/1/")
        self.assertEquals(Archive.objects.get(id=1).submitter_name, "Alex")


class MultipleUploadTestCase(TestCase):
    def test_upload_archive(self):
        c = Client()
        with open("/opt/inspector/.local/test_archives/ot.log") as fp:
            response = c.post("/upload/", {
                "name": "Alex",
                "site_name": "Michigan",
                "archive_identifier": "Test Archive",
                "taser_ticket_number": "444",
                "upload_another": "yes",
                "doc_file": fp
            })
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Archive.objects.get(id=1).submitter_name, "Alex")

        with open("/opt/inspector/.local/test_archives/ot.log") as fp:
            response = c.post("/upload/", {
                "name": "Brad",
                "site_name": "Michigan",
                "archive_identifier": "Test Archive",
                "taser_ticket_number": "444",
                "upload_another": "no",
                "doc_file": fp
            })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response["Location"], "/report/2/")
        self.assertEquals(Archive.objects.get(id=2).submitter_name, "Brad")
