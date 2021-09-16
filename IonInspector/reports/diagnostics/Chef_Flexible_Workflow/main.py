#!/usr/bin/env python
import os
import sys

from IonInspector.reports.diagnostics.common.inspector_utils import (
    get_xml_from_run_log,
    print_na,
    print_alert,
    write_results_from_template,
    print_ok,
    handle_exception,
    get_lines_from_chef_gui_logs,
    parse_run_date_from_xml_path,
    get_chef_run_log_xml_path,
)


def get_gui_log_lines_for_run(parsed_lines, run_start_date):
    pre_start_lines = []
    post_start_lines = []

    # Get the line index where our run started
    for i, line in enumerate(parsed_lines):
        line_level, line_date, line_message = line
        if "Starting RUN" in line_message:
            # We only have min resolution on the start date atm
            # and I want to allow some wiggle from when the start is logged in the gui to when its logged in the
            # xml, so I have to use something over 60 seconds here!
            if abs((line_date - run_start_date).total_seconds()) < 65:
                break
    else:
        raise ValueError(
            "Could not find run start in gui logs with start date: {}".format(
                run_start_date
            )
        )

    # Now get all the lines before and after until any other run
    for line_level, line_date, line_message in parsed_lines[i - 1 : 0 : -1]:
        if "Starting RUN" in line_message:
            break
        else:
            pre_start_lines.insert(0, (line_level, line_date, line_message))
    for line_level, line_date, line_message in parsed_lines[i + 1 :]:
        if "Starting RUN" in line_message:
            break
        else:
            post_start_lines.append((line_level, line_date, line_message))

    return pre_start_lines, post_start_lines


def get_solutions_and_reagents_serials(parsed_log_lines):
    solutions = None
    reagents = None
    for _, _, line_message in parsed_log_lines:
        if "parseLoadCheckdata" in line_message:
            if "chefSolutionsSerial" in line_message:
                _, i = line_message.split("=")
                solutions = i.strip().strip("()")
            elif "chefReagentsSerial" in line_message:
                _, i = line_message.split("=")
                reagents = i.strip().strip("()")
            if solutions and reagents:
                return solutions, reagents
    raise ValueError("Could not find solutions and reagents!")


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        # test for existance of the chef log
        root = get_xml_from_run_log(archive_path)

        kit_customer_facing_name_element = root.find("RunInfo/kit_customer_facing_name")
        kit_customer_facing_name_tag = (
            kit_customer_facing_name_element.text
            if kit_customer_facing_name_element is not None
            else ""
        )
        if kit_customer_facing_name_tag != "Ion 550 Kit-Chef":
            return print_na("Only runs for Ion 550 Kits")

        # attempt get the xml nodes relative to the flexible workflow stuff
        flexible = root.find("RunInfo/flexible")
        if flexible is None:
            return print_na(
                "The chef logs do not contain flexible workflow information."
            )
        hours_since_reagent_first_use = root.find(
            "RunInfo/hoursSinceReagentFirstUse"
        ).text.strip()
        hours_since_solution_first_use = root.find(
            "RunInfo/hoursSinceSolutionFirstUse"
        ).text.strip()
        num_previous_uses_reagent = root.find(
            "RunInfo/numPreviousUsesReagent"
        ).text.strip()
        num_previous_uses_solution = root.find(
            "RunInfo/numPreviousUsesSolution"
        ).text.strip()

        failed_reagents = 8 * 24 < int(hours_since_reagent_first_use)
        failed_solution = 8 * 24 < int(hours_since_solution_first_use)

        # solutions_serial, reagents_serial from gui log
        run_log_path = get_chef_run_log_xml_path(archive_path)
        run_date = parse_run_date_from_xml_path(run_log_path)
        gui_log_lines = get_lines_from_chef_gui_logs(archive_path)
        pre_run_lines, post_run_lines = get_gui_log_lines_for_run(
            gui_log_lines, run_date
        )
        solutions_serial, reagents_serial = get_solutions_and_reagents_serials(
            pre_run_lines
        )

        # construct the context and result html
        context = {
            "days_since_reagent_first_use": float(hours_since_reagent_first_use) / 24.0,
            "days_since_solution_first_use": float(hours_since_solution_first_use)
            / 24.0,
            "num_previous_uses_reagent": num_previous_uses_reagent,
            "num_previous_uses_solution": num_previous_uses_solution,
            "failed_reagents": failed_reagents,
            "failed_solution": failed_solution,
            "solutions_serial": solutions_serial,
            "reagents_serial": reagents_serial,
        }
        write_results_from_template(
            context, output_path, os.path.dirname(os.path.realpath(__file__))
        )

        # detect failures or success
        if failed_solution and failed_reagents:
            return print_alert(
                "Both the reagents and solutions were to old: "
                + hours_since_reagent_first_use
                + "/"
                + hours_since_solution_first_use
                + " hours."
            )
        if failed_reagents:
            return print_alert(
                "Reagents were to old: " + hours_since_reagent_first_use + " hours."
            )
        if failed_solution:
            return print_alert(
                "Solutions were to old: " + hours_since_reagent_first_use + " hours."
            )
        return print_ok("Flexible workflow used before day eight.")

    except OSError:
        return print_na("No chef logs to investigate.")

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
