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
        archive = Archive.objects.latest("id")
        self.assertEquals(response["Location"], "/report/{}/".format(archive.id))
        self.assertEquals(archive.submitter_name, "Alex")

        # check the report page loads
        response = c.get("/report/{}/".format(archive.id))
        self.assertEquals(response.status_code, 200)


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
        archive1 = Archive.objects.latest("id")
        self.assertEquals(archive1.submitter_name, "Alex")

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
        archive2 = Archive.objects.latest("id")
        self.assertEquals(archive2.submitter_name, "Brad")
        self.assertEquals(response["Location"], "/report/{}/".format(archive2.id))

        # check the report page loads
        response = c.get("/report/{}/".format(archive1.id))
        self.assertEquals(response.status_code, 200)

        response = c.get("/report/{}/".format(archive2.id))
        self.assertEquals(response.status_code, 200)


class SearchTestCase(TestCase):
    fixtures = ["search"]

    def test_find_archives_by_identifier_one(self):
        c = Client()
        response = c.get("/reports/?identifier=Soul")
        self.assertEquals(response.status_code, 200)
        self.assertIn("Troubled Soul", response.content)
        self.assertIn("Lost Soul", response.content)

    def test_find_archives_by_identifier_many(self):
        c = Client()
        response = c.get("/reports/?identifier=Troubled")
        self.assertEquals(response.status_code, 200)
        self.assertIn("Troubled Soul", response.content)
        self.assertNotIn("Lost Soul", response.content)

    def test_find_archives_by_submitter_many(self):
        c = Client()
        response = c.get("/reports/?submitter_name=Billy")
        self.assertEquals(response.status_code, 200)
        self.assertIn("Troubled Soul", response.content)
        self.assertIn("Lost Soul", response.content)

    def test_find_archives_by_tag(self):
        c = Client()
        response = c.get("/reports/?tags=550")
        self.assertEquals(response.status_code, 200)
        self.assertIn("Rerun Test", response.content)
        self.assertNotIn("Lost Soul", response.content)

    def test_find_archives_by_multiple_tags(self):
        c = Client()
        response = c.get("/reports/?tags=550&tags=Test")
        self.assertEquals(response.status_code, 200)
        self.assertIn("Rerun Test", response.content)
        self.assertNotIn("Lost Soul", response.content)
