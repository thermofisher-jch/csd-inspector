from django.test import SimpleTestCase
from datetime import datetime

from reports.diagnostics.Chef_Flexible_Workflow.main import get_solutions_and_reagents_serials, get_gui_log_lines_for_run


class ChefFlexibleWorkflowTestCase(SimpleTestCase):
    def test_get_run_lines(self):
        log_lines = [
            "[RS]-[INFO]:2018-08-02 12:54:13,194: ******* Starting RUN!...",
            "[BC]-[INFO]:2018-08-08 15:53:15,400: parseLoadCheckdata: (chefSolutionsSerial) = (12346150)",
            "[BC]-[INFO]:2018-08-08 15:53:16,914: parseLoadCheckdata: (chefReagentsSerial) = (12347573)",
            "[RS]-[INFO]:2018-08-13 15:54:14,194: ******* Starting RUN!...",
            "[OTUtility]-[INFO]:2018-08-13 15:54:14,197:  getTemplateSizeFlag:, in Boolean:0 for kit:s550_1",
            "[PlanStatus]-[INFO]:2018-08-13 15:54:14,298: ******* in planDetailCallback  id 1= 139",
            "[RS]-[INFO]:2018-08-17 12:54:13,194: ******* Starting RUN!...",
            "[PlanStatus]-[INFO]:2018-08-17 15:54:14,298: ******* in planDetailCallback  id 1= 139",
        ]
        pre_run_lines, post_run_lines = get_gui_log_lines_for_run(log_lines, datetime(2018, 8, 13, 15, 54, 14))
        self.assertEquals(pre_run_lines, [
            (
                "[BC]-[INFO]",
                datetime(2018, 8, 8, 15, 53, 15),
                " parseLoadCheckdata: (chefSolutionsSerial) = (12346150)"
            ),
            (
                "[BC]-[INFO]",
                datetime(2018, 8, 8, 15, 53, 16),
                " parseLoadCheckdata: (chefReagentsSerial) = (12347573)"
            )])
        self.assertEquals(post_run_lines, [
            (
                "[OTUtility]-[INFO]",
                datetime(2018, 8, 13, 15, 54, 14),
                "  getTemplateSizeFlag:, in Boolean:0 for kit:s550_1"
            ),
            (
                "[PlanStatus]-[INFO]",
                datetime(2018, 8, 13, 15, 54, 14),
                " ******* in planDetailCallback  id 1= 139"
            )])

    def test_get_solutions_and_reagents_serials(self):
        self.assertEquals(
            get_solutions_and_reagents_serials([
                (
                    "[BC]-[INFO]",
                    datetime(2018, 8, 8, 15, 53, 15),
                    " parseLoadCheckdata: (chefSolutionsSerial) = (12346150)"
                ),
                (
                    "[BC]-[INFO]",
                    datetime(2018, 8, 8, 15, 53, 16),
                    " parseLoadCheckdata: (chefReagentsSerial) = (12347573)"
                )]),
            ("12346150", "12347573")
        )
