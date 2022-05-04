#!/usr/bin/env python

import os
import csv
import copy
import datetime
import matplotlib
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    matplotlib.use('Agg')
import logging
import fnmatch
import matplotlib.pyplot as plt
import json
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
    font = {"family": "sans-serif", "weight": "normal", "size": 10}
    matplotlib.rc("font", **font)
    
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
                        
    for file in "initFill_R1","initFill_R2","initFill_R3","initFill_R4","initFill_RW1":
        fileName=os.path.join(os.path.join(archive_path, "CSA"),file)+".csv"
        if os.path.exists(fileName):
            x = []
            y1 = []
            y2 = []
  
            with open(fileName,'r') as csvfile:
                lines = csv.reader(csvfile, delimiter=',')
                for row in lines:
                    x.append(float(row[5]))
                    y1.append(float(row[9]))
                    y2.append(float(row[13]))
                fig=plt.figure()
                fig1 = fig.add_subplot(111)
                plt.plot(x, y1, color = 'g', linestyle = 'dashed',
                   marker = 'o',label = "WD1")
                plt.plot(x, y2, color = 'r', linestyle = 'dashed',
                   marker = 'o',label = "WD2")

                plt.xticks(rotation = 25)
                plt.xlabel('Time')
                plt.ylabel('FlowRate')
                plt.title(file, fontsize = 20)
                plt.grid()
                plt.legend()
                plt.savefig(os.path.join(output_path,file)+".png")
            
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
        
