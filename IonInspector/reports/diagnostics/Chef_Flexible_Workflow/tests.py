from django.test import SimpleTestCase
from datetime import datetime

from reports.diagnostics.Chef_Flexible_Workflow.main import (
    get_solutions_and_reagents_serials,
    get_gui_log_lines_for_run,
)


class ChefFlexibleWorkflowTestCase(SimpleTestCase):
    def test_get_run_lines(self):
        log_lines = [
            [
                "[RS]-[INFO]",
                datetime(2018, 8, 02, 12, 54, 13),
                "******* Starting RUN!...",
            ],
            [
                "[BC]-[INFO]",
                datetime(2018, 8, 8, 15, 53, 15),
                " parseLoadCheckdata: (chefSolutionsSerial) = (12346150)",
            ],
            [
                "[BC]-[INFO]",
                datetime(2018, 8, 8, 15, 53, 16),
                " parseLoadCheckdata: (chefReagentsSerial) = (12347573)",
            ],
            [
                "[RS]-[INFO]",
                datetime(2018, 8, 13, 15, 54, 14),
                " ******* Starting RUN!...",
            ],
            [
                "[OTUtility]-[INFO]",
                datetime(2018, 8, 13, 15, 54, 14),
                "  getTemplateSizeFlag:, in Boolean:0 for kit:s550_1",
            ],
            [
                "[PlanStatus]-[INFO]",
                datetime(2018, 8, 13, 15, 54, 14),
                " ******* in planDetailCallback  id 1= 139",
            ],
            [
                "[RS]-[INFO]",
                datetime(2018, 8, 17, 12, 54, 13),
                " ******* Starting RUN!...",
            ],
            [
                "[PlanStatus]-[INFO]",
                datetime(2018, 8, 17, 15, 54, 14),
                " ******* in planDetailCallback  id 1= 139",
            ],
        ]
        pre_run_lines, post_run_lines = get_gui_log_lines_for_run(
            log_lines, datetime(2018, 8, 13, 15, 54, 14)
        )
        self.assertEquals(
            pre_run_lines,
            [
                (
                    "[BC]-[INFO]",
                    datetime(2018, 8, 8, 15, 53, 15),
                    " parseLoadCheckdata: (chefSolutionsSerial) = (12346150)",
                ),
                (
                    "[BC]-[INFO]",
                    datetime(2018, 8, 8, 15, 53, 16),
                    " parseLoadCheckdata: (chefReagentsSerial) = (12347573)",
                ),
            ],
        )
        self.assertEquals(
            post_run_lines,
            [
                (
                    "[OTUtility]-[INFO]",
                    datetime(2018, 8, 13, 15, 54, 14),
                    "  getTemplateSizeFlag:, in Boolean:0 for kit:s550_1",
                ),
                (
                    "[PlanStatus]-[INFO]",
                    datetime(2018, 8, 13, 15, 54, 14),
                    " ******* in planDetailCallback  id 1= 139",
                ),
            ],
        )

    def test_get_solutions_and_reagents_serials(self):
        self.assertEquals(
            get_solutions_and_reagents_serials(
                [
                    (
                        "[BC]-[INFO]",
                        datetime(2018, 8, 8, 15, 53, 15),
                        " parseLoadCheckdata: (chefSolutionsSerial) = (12346150)",
                    ),
                    (
                        "[BC]-[INFO]",
                        datetime(2018, 8, 8, 15, 53, 16),
                        " parseLoadCheckdata: (chefReagentsSerial) = (12347573)",
                    ),
                ]
            ),
            ("12346150", "12347573"),
        )
