#!/usr/bin/env python

import os,sys
from datetime import datetime, date
import logging
from reports.diagnostics.common.inspector_utils import *

logger = logging.getLogger(__name__)


def parse_start_time(start_time_string):
    date_format = "%m/%d/%Y %H:%M:%S"
    return datetime.strptime(start_time_string, date_format).date()


def reagents_expired(run_date, reagent_exp_dates):
    for exp_date in reagent_exp_dates:
        if isinstance(exp_date, date) and exp_date.replace(day=1) < run_date.replace(
            day=1
        ):
            return True

    return False


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        data = read_explog(archive_path)
        check_supported(data)

        # read all the lines into an array
        if archive_type == "Valkyrie":
            path = os.path.join(archive_path, "CSA", "InitLog.txt")
        else:
            path = os.path.join(archive_path, "InitLog.txt")
        with open(path) as f:
            lines = f.readlines()

        # parse products from lines
        products = parse_init_log(lines)

        # read in carry forward
        base_caller = read_base_caller_json(archive_path, archive_type)
        cf = float(base_caller["Phasing"]["CF"]) * 100

        # read in run date
        explog = read_explog(archive_path)
        run_date = parse_start_time(explog.get("Start Time", None))

        # construct the html response message
        cleaning_dict = {}
        for key, value in products.iteritems():
            if "cleaning" in key.lower():
                cleaning_dict = value

        sequencing_dict = {}
        for key, value in products.iteritems():
            if "sequencing" in key.lower():
                sequencing_dict = value

        wash_dict = {}
        for key, value in products.iteritems():
            if "wash" in key.lower():
                wash_dict = value

        message = " | ".join(
            [
                "Cleaning Lot %s" % cleaning_dict.get("lotNumber", "Unknown"),
                "Reagents Lot %s" % sequencing_dict.get("lotNumber", "Unknown"),
                "Wash Lot %s" % wash_dict.get("lotNumber", "Unknown"),
            ]
        )

        # write out results.html
        with open(os.path.join(output_path, "results.html"), "w") as html_handle:
            # html header
            html_handle.write("<html><head></head><body>")

            # write out reagent image
            if os.path.exists(os.path.join(archive_path, "InitRawTrace0.png")):
                html_handle.write("<h2 align='center'>Reagent Check</h2>")
                html_handle.write("<p style='text-align:center;'>")
                html_handle.write("<img src='../../InitRawTrace0.png' />")
                html_handle.write("</p>")

            # write out carry forward for checking reagent leaks
            html_handle.write("<h2 align='center'>Phasing - Carry Forward</h2>")
            html_handle.write("<p style='text-align:center;'>")
            html_handle.write("CF = {0:.2f}%".format(cf))
            html_handle.write("</p>")

            # write out reagent details
            for title, reagent_dict in [
                ("Cleaning", cleaning_dict),
                ("Reagents", sequencing_dict),
                ("Wash", wash_dict),
            ]:
                html_handle.write("<h2 align='center'>%s</h2>" % title)
                html_handle.write("<p style='text-align:center;'>")
                html_handle.write("%s<br>" % reagent_dict.get("productDesc"))
                html_handle.write("Lot: %s<br>" % reagent_dict.get("lotNumber"))

                reagent_exp_date = reagent_dict.get("expDate", "Unknown")
                if isinstance(reagent_exp_date, date):
                    days_until_expiration = None
                    if reagent_exp_date and run_date:
                        days_until_expiration = (reagent_exp_date - run_date).days
                    html_handle.write(
                        "Expiration Date: %s<br>"
                        % reagent_exp_date.strftime("%Y/%m/%d")
                    )

                    if days_until_expiration < 0:
                        html_handle.write(
                            "<span style='color:red'>Run %i days after expiration.</span><br>"
                            % abs(days_until_expiration)
                        )
                    else:
                        html_handle.write(
                            "Run %i days before expiration.<br>"
                            % abs(days_until_expiration)
                        )
                else:
                    html_handle.write(
                        "Expiration Date: <b>%s</b><br>" % reagent_exp_date
                    )

                html_handle.write("</p>")

            # html footer
            html_handle.write("</body></html>")

        # convert the pdf to usable png and text files
        if os.path.exists(archive_path+"/report.pdf"):
            
            cmd="mutool convert -o {}/report_.png {}/report.pdf 1".format(output_path,archive_path)
            logger.warn(cmd)
            os.system(cmd)
            cmd="mutool convert -o {}/report_1.txt {}/report.pdf 1".format(output_path,archive_path)
            logger.warn(cmd)
            os.system(cmd)
            cmd="mkdir {}/../Genexus_Lane_Activity; convert {}/report_1.png -crop 120x82+110+305 {}/../Genexus_Lane_Activity/Bead_density_1000.png".format(output_path,output_path,output_path)
            logger.warn(cmd)
            os.system(cmd)

        # determine if reagents were expired when the run was executed
        if run_date and cleaning_dict and wash_dict and sequencing_dict:
            if reagents_expired(
                run_date,
                [
                    cleaning_dict["expDate"],
                    sequencing_dict["expDate"],
                    wash_dict["expDate"],
                ],
            ):
                return print_alert(message + " | EXPIRED")
            else:
                return print_ok(message)
        else:
            return print_alert(message)

    except Exception as exc:
        return handle_exception(exc, output_path)


if __name__ == "__main__":
    execute(sys.argv[1], sys.argv[2], sys.argv[3])
