from django.core.files.base import ContentFile
from django.test import Client, TestCase

from reports.models import Archive


class ArchiveAPITestCase(TestCase):
    fixtures = ["search"]

    def test_upload_archive(self):
        c = Client()
        response = c.get("/api/v1/Archive/values/?field=site&q=Al")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()["values"], ["Alabama"])

    def test_rerun_archive(self):
        archive = Archive.objects.get(id=3)
        archive.doc_file.save("ot.log", ContentFile(""))
        archive.diagnostics.all().delete()

        c = Client()
        response = c.post("/api/v1/Archive/rerun/3/")

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response["Location"], "/report/3/")
        self.assertTrue(archive.diagnostics.count() > 0)

    def test_delete_archive(self):
        c = Client()
        response = c.post("/api/v1/Archive/remove/3/")

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response["Location"], "/reports/")
        self.assertEquals(Archive.objects.filter(id=3).count(), 0)