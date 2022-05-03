# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import csv
import json
import fnmatch
import copy
import logging
import datetime
from reports.diagnostics.common.inspector_utils import (
    print_info,
    print_alert,
    print_ok,
    write_results_from_template,
)

logger = logging.getLogger(__name__)

def get_other_details(rows):
    other_runDetails = {}
    consumable = "Consumable Information"
    reagent = "Reagent Information"
    for row in rows:
        if reagent in row:
            other_runDetails[reagent] = []
            continue
        if (
            reagent in other_runDetails
            and consumable not in row
            and consumable not in other_runDetails
        ):
            other_runDetails[reagent].append(row)
        if consumable in row:
            other_runDetails[consumable] = []
            continue
        if consumable in other_runDetails and "Analysis" not in row:
            other_runDetails[consumable].append(row)
        if "Analysis" in row:
            break
    return other_runDetails


def execute(archive_path, output_path, archive_type):
    expired=False
    runDateTxt=""
    lastInitDateTxt=""
    InitMsg=""
    infoRowsForOtherDetails = None
    for root, dirnames, filenames in os.walk(os.path.join(archive_path, "CSA")):
        for filename in fnmatch.filter(filenames, "Info.csv"):
            with open(os.path.join(root, filename), "rb") as fp:
                info_rows = list(csv.reader(fp, delimiter=","))
                infoRowsForOtherDetails = copy.deepcopy(info_rows)

    if os.path.exists(os.path.join(archive_path, "CSA/explog_final.json")):
        with open(os.path.join(archive_path, "CSA/explog_final.json"), "rb") as fp:
            exp = json.load(fp)
            if "Start Time" in exp:
                runDateTxt=exp["Start Time"]
            if "last_init_date" in exp:
                lastInitDateTxt=exp["last_init_date"]

    if runDateTxt=="" and os.path.exists(os.path.join(archive_path, "CSA/explog.json")):
        with open(os.path.join(archive_path, "CSA/explog.json"), "rb") as fp:
            exp = json.load(fp)
            if "Start Time" in exp:
                runDateTxt=exp["Start Time"]
            if "last_init_date" in exp:
                lastInitDateTxt=exp["last_init_date"]        
        
        
    if runDateTxt != "" and os.path.exists(os.path.join(archive_path, "CSA/DeckStatus.json")):
        logger.warn("runDateTxt "+runDateTxt)
        runDateObj = datetime.datetime.strptime(runDateTxt,"%m/%d/%Y %H:%M:%S")
        runDate = int(runDateObj.strftime("%y%m%d"))
        
        lastInitDate=0
        if lastInitDateTxt != "":
            logger.warn("lastInitDateTxt "+lastInitDateTxt)
            lastInitDateObj = datetime.datetime.strptime(lastInitDateTxt,"%Y/%m/%d %H:%M:%S")
            lastInitDate = int(lastInitDateObj.strftime("%y%m%d"))
            firstInitThr=int((lastInitDateObj+datetime.timedelta(days=14)).strftime("%y%m%d"))
            secondInitThr=int((lastInitDateObj+datetime.timedelta(days=28)).strftime("%y%m%d"))
            logger.warn("thr1: {}".format(firstInitThr))
            logger.warn("thr2: {}".format(secondInitThr))
            if runDate > secondInitThr:
                InitMsg="Init more than 28 days old"
            elif runDate > firstInitThr:
                InitMsg="Init more than 14 days old"
            
        
        logger.warn("run:  {}".format(runDate))
        with open(os.path.join(archive_path, "CSA/DeckStatus.json"), "rb") as fp:
            cons = json.load(fp)
            for consItem in cons:
                if "barcodeList" in consItem:
                    for bcItem in consItem["barcodeList"]:
                        if "expiryDate" in bcItem:
                            expDate=int(bcItem["expiryDate"])
                            logger.warn("found {} < {}".format(expDate,runDate))
                            if expDate < runDate:
                                expired=True
                        
            
        
    write_results_from_template(
        {"other_runDetails": get_other_details(infoRowsForOtherDetails)},
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )

    if not expired and InitMsg=="":
        return print_ok("See results for details. (ok)")
    else:
        msg="See results for details."
        if expired:
            msg+=" **Expired consumables detected**"
        msg+=InitMsg
        
        return print_alert(msg)
        
