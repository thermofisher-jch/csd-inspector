#!/usr/bin/env python

import sys
from IonInspector.reports.diagnostics.common.inspector_utils import *


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        # test for existance of the chef log
        root = get_xml_from_run_log(archive_path)

        kit_customer_facing_name_element = root.find("RunInfo/kit_customer_facing_name")
        kit_customer_facing_name_tag = kit_customer_facing_name_element.text if kit_customer_facing_name_element is not None else ''
        if kit_customer_facing_name_tag != "Ion 550 Kit-Chef":
            return print_na("Only runs for Ion 550 Kits")

        # attempt get the xml nodes relative to the flexible workflow stuff
        flexible = root.find("RunInfo/flexible")
        if flexible is None:
            return print_na("The chef logs do not contain flexible workflow information.")
        hours_since_reagent_first_use = root.find("RunInfo/hoursSinceReagentFirstUse").text.strip()
        hours_since_solution_first_use = root.find("RunInfo/hoursSinceSolutionFirstUse").text.strip()
        num_previous_uses_reagent = root.find("RunInfo/numPreviousUsesReagent").text.strip()
        num_previous_uses_solution = root.find("RunInfo/numPreviousUsesSolution").text.strip()

        failed_reagents = 8 * 24 < int(hours_since_reagent_first_use)
        failed_solution = 8 * 24 < int(hours_since_solution_first_use)

        # construct the context and result html
        context = {
            'days_since_reagent_first_use': float(hours_since_reagent_first_use) / 24.0,
            'days_since_solution_first_use': float(hours_since_solution_first_use) / 24.0,
            'num_previous_uses_reagent': num_previous_uses_reagent,
            'num_previous_uses_solution': num_previous_uses_solution,
            'failed_reagents': failed_reagents,
            'failed_solution': failed_solution,
        }
        write_results_from_template(context, output_path, os.path.dirname(os.path.realpath(__file__)))

        # detect failures or success
        if failed_solution and failed_reagents:
            return print_alert("Both the reagents and solutions were to old: " + hours_since_reagent_first_use + "/" + hours_since_solution_first_use + " hours.")
        if failed_reagents:
            return print_alert("Reagents were to old: " + hours_since_reagent_first_use + " hours.")
        if failed_solution:
            return print_alert("Solutions were to old: " + hours_since_reagent_first_use + " hours.")
        return print_ok("Flexible workflow used before day eight.")

    except OSError:
        return print_na("No chef logs to investigate.")

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
