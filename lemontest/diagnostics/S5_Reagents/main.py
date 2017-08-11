#!/usr/bin/env python

import sys
from datetime import datetime

from lemontest.diagnostics.common.inspector_utils import *


def parse_init_log(log_lines):
    date_formats = {
        "expDate": "%Y/%m/%d"
    }
    product_dict = {}
    current_product = None
    for line in log_lines:
        if line.startswith("productDesc: "):
            # start of block we want to parse
            current_product = line.split(":", 1)[1].strip()
            product_dict[current_product] = {}
        elif line.startswith("remainingUses: "):
            # end of block we want to parse
            product_dict[current_product]["remainingUses"] = line.split(":", 1)[1].strip()
            current_product = None
        elif current_product:
            # in block we want to parse
            key, value = line.split(":", 1)
            if key in date_formats:
                product_dict[current_product][key] = datetime.strptime(value.strip(), date_formats[key]).date()
            else:
                product_dict[current_product][key] = value.strip()
    return product_dict


def parse_start_time(start_time_string):
    date_format = "%m/%d/%Y %H:%M:%S"
    return datetime.strptime(start_time_string, date_format).date()


def reagents_expired(run_date, reagent_exp_dates):
    for exp_date in reagent_exp_dates:
        if exp_date <= run_date:
            return True
    else:
        return False


def execute(archive_path, output_path, archive_type):
    """Executes the test"""
    try:
        data = read_explog(archive_path)
        check_supported(data)

        # read all the lines into an array
        with open(os.path.join(archive_path, "InitLog.txt")) as f:
            lines = f.readlines()

        # parse products from lines
        products = parse_init_log(lines)

        # read in carry forward
        base_caller = read_base_caller_json(archive_path)
        cf = float(base_caller["Phasing"]["CF"]) * 100

        # read in run date
        explog = read_explog(archive_path)
        run_date = parse_start_time(explog.get('Start Time', None))

        # construct the html response message
        cleaning_dict = products.get('Ion S5 Cleaning Solution', {})

        sequencing_dict = {}
        for key in ["Ion S5 Sequencing Reagents", "Ion S5 Sequencing Reagent",
                    "Ion S5 ExT Sequencing Reagent", "Ion S5 ExT Sequencing Reagents"]:
            if key in products:
                sequencing_dict = products[key]
                break

        wash_dict = {}
        for key in ["Ion S5 Wash Solution", "Ion S5 ExT Wash Solution"]:
            if key in products:
                wash_dict = products[key]
                break

        message = " | ".join([
            "Cleaning Lot <strong>%s</strong>" % cleaning_dict["lotNumber"],
            "Reagents Lot <strong>%s</strong>" % sequencing_dict["lotNumber"],
            "Wash Lot <strong>%s</strong>" % wash_dict["lotNumber"],
        ])

        # determine if reagents were expired when the run was executed
        if run_date and cleaning_dict and wash_dict and sequencing_dict:
            if reagents_expired(run_date, [cleaning_dict["expDate"], sequencing_dict["expDate"], wash_dict["expDate"]]):
                print_alert(message + " | Expired Reagents")
            else:
                print_info(message)
        else:
            print_alert(message)

        # write out results.html
        with open(os.path.join(output_path, "results.html"), "w") as html_handle:
            # html header
            html_handle.write("<html><head></head><body>")

            # write out reagent image
            if os.path.exists(os.path.join(archive_path, 'InitRawTrace0.png')):
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
                days_until_expiration = None
                if reagent_dict["expDate"] and run_date:
                    days_until_expiration = (reagent_dict["expDate"] - run_date).days

                html_handle.write("<h2 align='center'>%s</h2>" % title)
                html_handle.write("<p style='text-align:center;'>")
                html_handle.write("Lot: %s<br>" % reagent_dict["lotNumber"])
                html_handle.write("Expiration Date: %s<br>" % reagent_dict["expDate"].strftime('%Y/%m/%d'))

                if days_until_expiration < 0:
                    html_handle.write(
                        "<span style='color:red'>Run %i days after expiration.</span><br>" % abs(days_until_expiration)
                    )
                else:
                    html_handle.write(
                        "Run %i days before expiration.<br>" % abs(days_until_expiration)
                    )

                html_handle.write("</p>")

            # html footer
            html_handle.write("</body></html>")

    except Exception as exc:
        handle_exception(exc, output_path)

if __name__ == "__main__":
    archive_path, output_path, archive_type = sys.argv[1:4]
    execute(archive_path, output_path, archive_type)