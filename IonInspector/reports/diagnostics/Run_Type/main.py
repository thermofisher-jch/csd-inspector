#!/usr/bin/env python

import os
import json
import logging
import csv

from reports.diagnostics.common.inspector_utils import (
    read_explog,
    shutil,
    print_info,
    print_ok,
    print_alert,
    write_results_from_template
)
logger = logging.getLogger(__name__)

def CheckValkWf(archive_path):
    rc = ""
    vwfPath=os.path.join(archive_path, "ValkyrieWorkflow/results.json")
    if os.path.exists(vwfPath):
        with open(vwfPath,"r") as fp:
            vwfp = json.load(fp)
            if "vacLog" in vwfp and "pipette_errors" in vwfp:
                # 6.6 and higher
                if "bottomlog" in vwfp and "missed_bottom_p1_count" in vwfp["bottomlog"]:
                    bottomFail = vwfp["bottomlog"]["missed_bottom_p1_count"] + \
                        vwfp["bottomlog"]["missed_bottom_p2_count"]
                        
                    if bottomFail > 0:
                        rc += " check bottom failures"

                    bentFail = vwfp["bottomlog"]["bent_tips_count"]
                    if bentFail > 0:
                        rc += " check bent tips"
                        

                
                if "er52" in  vwfp and "pipette_1" in vwfp["er52"]:
                    pipErr52 = vwfp["er52"]["pipette_1"] + \
                        vwfp["er52"]["pipette_2"] + \
                        vwfp["pipette_errors"]["pipette_1"]["count"] + \
                        vwfp["pipette_errors"]["pipette_2"]["count"]
                        
                    if pipErr52 > 0:
                        rc += " check pip err"
                
                if "tip_pickup_errors" in vwfp and "p1" in vwfp["tip_pickup_errors"] and "struggle_count" in vwfp["tip_pickup_errors"]["p1"]:
                    tipPickupErrors = vwfp["tip_pickup_errors"]["p1"]["struggle_count"] + vwfp["tip_pickup_errors"]["p1"]["unable_count"] + \
                        vwfp["tip_pickup_errors"]["p2"]["struggle_count"] + vwfp["tip_pickup_errors"]["p2"]["unable_count"]
                    if  tipPickupErrors > 0:
                        rc += " check tip pickup"

                if "blocked_tips" in vwfp:
                    blockedCount = vwfp["blocked_tips"]["p2_count"] + vwfp["blocked_tips"]["p1_count"]
                    if  blockedCount > 0:
                        rc += " check blocked tips"
                
                for lane in 0,1,2,3,4:
                    laneData=vwfp["vacLog"]["lane "+str(lane)]
            
                    if "postLib_suspected_leaks_count" in laneData and \
                       "postLib_suspected_clogs_count" in laneData and \
                       "suspected_leaks_count" in laneData and \
                       "suspected_clogs_count" in laneData:
                        VacFail = int(laneData["postLib_suspected_leaks_count"]) + \
                                           int(laneData["postLib_suspected_clogs_count"]) + \
                                           int(laneData["suspected_leaks_count"]) + \
                                           int(laneData["suspected_clogs_count"])
                        if VacFail > 0:
                            rc += " check postlib"
                if "conical_clog_check" in vwfp:
                    clogCnt=0                           
                    for conical in "RG","RC","RA","RT","W1":
                        if vwfp["conical_clog_check"]["conical"][conical]["is_clogged"]:
                            clogCnt+=1
                    if clogCnt > 0:
                        rc += " check conical clog"
                
                if "pipPresTest" in vwfp:
                    failCnt = vwfp["pipPresTest"]["vacTest_fail"]["p1_count"] + \
                        vwfp["pipPresTest"]["vacTest_fail"]["p2_count"] + \
                        vwfp["pipPresTest"]["waterWell_fail"]["p1_count"] + \
                        vwfp["pipPresTest"]["waterWell_fail"]["p2_count"] + \
                        vwfp["pipPresTest"]["inCoupler_fail"]["p1_count"] + \
                        vwfp["pipPresTest"]["inCoupler_fail"]["p2_count"]
                    if failCnt > 0:
                        rc += " check pipPresTest"
                if rc == "":
                    rc = "ok"

        bottomLogFile=os.path.join(archive_path, "ValkyrieWorkflow") + "/TubeBottomLog.csv"
        if os.path.exists(bottomLogFile):
            with open(bottomLogFile,"r") as fp:
                badBottomCnt=0
                goodBottomCnt=0
                blog = list(csv.reader(fp, delimiter=","))
                for line in blog:
                    if len(line) >= 5 and "[" in line[5]:
                        numberstxt=line[5].replace("[","").replace("]","").split()
                        numbers=[float(bb) for bb in numberstxt]
                        for number in numbers:
                            if number >= 1.0 or number <= -1.0:
                                badBottomCnt+=1 
                            else:
                                goodBottomCnt+=1
                logger.warn("badCnt: {} goodCnt: {}".format(badBottomCnt,goodBottomCnt))
                if badBottomCnt > 0:
                    rc += " check tube bottom"


   
                
    rc = (rc[:60] + '...') if len(rc) > 60 else rc
    

    return rc 


def execute(archive_path, output_path, archive_type):
    explog = read_explog(archive_path)
    run_type = explog.get("RunType", "Unknown")
    message = "Run Type: {}  (".format(run_type)

    complete=False
    files = os.listdir(archive_path)
    for file in files:
        if ".CSA.txz" in file:
            complete=True

    if not complete:
        message = "****CSA downloaded before plugins completed. Please re-download the CSA for a more complete report.****"
        return print_alert(message)

    valkyrie_workflow_path = os.path.join(archive_path, "ValkyrieWorkflow") + "/"

    files = os.listdir(valkyrie_workflow_path)

    if "results.json" in files:
        files.remove("results.json")

    if "ValkyrieWorkflow_block.html" in files:
        files.remove("ValkyrieWorkflow_block.html")

    if os.path.exists(valkyrie_workflow_path + "ValkyrieWorkflow_block.html"):
        # we should check to see if there are any errors in the valkyrie workflow plugin
        message += CheckValkWf(archive_path)
        shutil.copy(
            valkyrie_workflow_path + "ValkyrieWorkflow_block.html",
            os.path.join(output_path, "results.html"),
        )
        os.system("sed -i 's/TubeBottomLog\.csv/TubeBottomLog\.html/g' {}".format(os.path.join(output_path, "results.html")))
        for file in files:
            try:
                shutil.copy(
                    valkyrie_workflow_path + file, os.path.join(output_path, file)
                )
            except IOError:
                pass
    message += ")"
    
    if os.path.exists(os.path.join(output_path, "TubeBottomLog.csv")):
        with open(os.path.join(output_path, "TubeBottomLog.csv"), "rb") as fp:
            summary={}
            support={}
            summary["BottomLog"] = list(csv.reader(fp, delimiter=","))
            write_results_from_template(
            {"other_runDetails": summary,
             "support": support},
            output_path,
            os.path.dirname(os.path.realpath(__file__)),
            "TubeBottomLog.html"
            )


        
    if "(ok) in message":
        return print_ok(message)
    else:
        return print_info(message)
