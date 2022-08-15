#!/usr/bin/env python
import os
import time
import csv
import fnmatch
import copy
import json
import logging
import re
import image_tests

from reports.diagnostics.common.inspector_utils import (
    read_explog,
    get_debug_path,
    print_info,
    print_alert,
    print_ok,
    write_results_from_template,
)
from django.conf import settings
from collections import OrderedDict, namedtuple
import subprocess

PASS = "Passed"
FAIL = "Failed"
NA = "Not Calculated"

AbortedChecks={}

id="Movement error on the z-drive"
AbortedChecks[id]={"errorReason":"Pipette Z motor failure",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Run the Pipette factory test",
                                                             "Retry the Run"]}

id="Checksum error in rtu mode"
AbortedChecks[id]={"errorReason":"Gantry X motor failure",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Check the X motor drive communications cable",
                                                          "Run the X motor factory test",
                                                          "Retry the Run"]}

id="ShuttleChip failed to Home"
AbortedChecks[id]={"errorReason":"Chip Shuttle failed to Home",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Run the Chip Shuttle factory test",
                                                          "Retry the Run"]}

id="pipette 1 returned error = Maximum volume in pipetting drive reached"  # error 54
AbortedChecks[id]={"errorReason":"Pipette 1 error detected",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["A replacement of the faulty pipette may be needed",
                                "Run deck cal, chip coupler test, pipette test"
                                                          "Retry the Run"]}

id="pipette 2 returned error = Maximum volume in pipetting drive reached"  # error 54
AbortedChecks[id]={"errorReason":"Pipette 2 error detected",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["A replacement of the faulty pipette may be needed",
                                "Run deck cal, chip coupler test, pipette test",
                                                          "Retry the Run"]}

id="unable to pickup tip"  # error 54
AbortedChecks[id]={"errorReason":"Pipette unable to pickup tip",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Run the Pipette factory test",
                                                    "Run DeckCal",
                                                    "Retry the Run"]}

id="pipette 1 returned error = Movement error on the z-drive"
AbortedChecks[id]={"errorReason":"Pipette 1 Internal Error",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Run the Pipette factory test",
                                                    "Run DeckCal",
                                                    "Retry the Run"]}

id="pipette 2 returned error = Movement error on the z-drive"
AbortedChecks[id]={"errorReason":"Pipette 2 Internal Error",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Run the Pipette factory test",
                                                    "Run DeckCal",
                                                    "Retry the Run"]}

id="Chip calibration failed"
AbortedChecks[id]={"errorReason":"Chip calibration failed",
                   "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Run Post Run Clean",
                                                    "Run the Fluidics factory test",
                                                    "Retry the Run"]}

logger = logging.getLogger(__name__)

def get_qc_dict(rows):
    #
    def init_d():
        return {"header": "", "type": "", "keys": [], "metrics": []}

    q = init_d()
    header = ""
    blank_cnt = 0
    start_metrics = False
    for row in rows:
        if len(row) == 0:
            blank_cnt += 1

            # metrics section ends when a blank line
            if start_metrics:
                yield q
                q = init_d()
                start_metrics = False
        else:
            blank_cnt = 0

        if blank_cnt > 1:
            # skip when multiple blank lines
            continue

        """
        # either it is header or type
        Sample QC Evaluation Metrics

        DNA

        Metric Name,Value,Reference Range,QC Status
        
        """
        if len(row) == 1:
            k = row.pop()
            if "QC" in k and k.endswith("Metrics"):
                header = k
                q = init_d()
                q["header"] = header
            else:
                q = init_d()
                q["header"] = header
                q["type"] = k

        """
        # when multiple element per lines, likely starting QC Metric Sections
        
        Metric Name,Value,Reference Range,QC Status
        Key Signal,55,Not Set,Not Calculated
        Percent Loading,90.6,Not Set,Not Calculated
        Raw Read Accuracy,98.6,Not Set,Not Calculated

        """
        if len(row) > 1:
            name = row[0]
            if name.startswith("Metric Name"):
                q["keys"] = row
                start_metrics = True
                continue

            if start_metrics:
                m = {}
                keys = q["keys"]
                for i, k in enumerate(keys):
                    m[k] = row[i]
                q["metrics"].append(m)


def find_sample_name(rows):
    for row in rows:
        if len(row) < 2:
            continue
        if "sample name" in row[0].lower():
            return row[1]
    return "Unknown Sample"


def runLevelQcData(qc_detail):
    section = qc_detail.get("header")  # section header, i.e. Run QC/ Control QC Metrics
    type_name = qc_detail.get("type")
    run_level_failedQc = 0
    run_level_data = {
        "qc_status": NA,
        "keys": [],
        "metrics": {},
    }

    if section not in run_level_data["metrics"]:
        run_level_data["metrics"][section] = []
    run_level_data["keys"] = qc_detail.get("keys")
    for m in qc_detail.get("metrics", []):
        run_level_data["qc_status"] = m["QC Status"]
        # any fail -> fail
        if m["QC Status"] == FAIL:
            run_level_failedQc += 1

        if type_name:
            m["Metric Name"] = "%s %s" % (type_name, m["Metric Name"])
        run_level_data["metrics"][section].append(m)
    return run_level_failedQc, run_level_data


def populate_samples(sample_name, rows):
    sample_data = {
        "sample_name": sample_name,
        "qc_status": NA,
        "keys": [],
        "metrics": {},
    }

    failed_samples = {
        "sample_name": sample_name,
        "qc_status": NA,
        "keys": [],
        "metrics": {},
    }

    runQc_data = {}
    run_level_failedQcs = {}
    controlQc_data = {}
    for qc_detail in get_qc_dict(rows):
        section = qc_detail.get("header")  # section header, i.e. Run QC Metrics
        type_name = qc_detail.get("type")

        if "Run QC" in section and not bool(runQc_data):
            run_level_failedQc, runQc_data = runLevelQcData(qc_detail)
            if run_level_failedQc:
                run_level_failedQcs["failedRunQc"] = run_level_failedQc
            continue

        if "Control QC" in section and not bool(controlQc_data):
            run_level_failedQc, controlQc_data = runLevelQcData(qc_detail)
            if run_level_failedQc:
                run_level_failedQcs["failedControlQc"] = run_level_failedQc
            continue

        # assuming all qc_details have the same keys, so last one gets used.
        sample_data["keys"] = qc_detail.get("keys")
        failed_samples["keys"] = qc_detail.get("keys")

        if section not in sample_data["metrics"]:
            sample_data["metrics"][section] = []

        for m in qc_detail.get("metrics", []):
            # any fail -> fail
            if m["QC Status"] == FAIL:
                sample_data["qc_status"] = FAIL
                failed_samples["qc_status"] = FAIL

            # set pass only when NA
            if m["QC Status"] == PASS and sample_data["qc_status"] == NA:
                sample_data["qc_status"] = PASS

            if type_name:
                m["Metric Name"] = "%s %s" % (type_name, m["Metric Name"])

            sample_data["metrics"][section].append(m)
            if m["QC Status"] == FAIL:
                if section not in failed_samples["metrics"]:
                    failed_samples["metrics"][section] = []
                failed_samples["metrics"][section].append(m)

    return sample_data, failed_samples, runQc_data, controlQc_data, run_level_failedQcs


def GetQCMetrics(archive_path, output_path, archive_type):    

    results = {"num_failed_samples": 0, "Samples_Passed": 0, "Samples_Failed": 0, "failedRunQc": 0, "failedControlQc": 0, "samples" : []}
    infoRowsForOtherDetails = None
    
    try:
        for root, dirnames, filenames in os.walk(os.path.join(archive_path, "CSA")):
            for filename in fnmatch.filter(filenames, "Info.csv"):
                if os.path.exists(os.path.join(root, filename)):
                    with open(os.path.join(root, filename), "rb") as fp:
                        info_rows = list(csv.reader(fp, delimiter=","))
                        sample_name = find_sample_name(info_rows)
        
                        infoRowsForOtherDetails = copy.deepcopy(info_rows)
                        (
                            sample_data,
                            failed_data,
                            runQc_data,
                            controlQc_data,
                            run_level_failedQcs,
                        ) = populate_samples(sample_name, info_rows)
        
                        results["samples"].append(sample_data)
    except:
        logger.warn("Exception in GetQCMetrics")
                    
    if run_level_failedQcs.get("failedRunQc", ""):
        results["failedRunQc"] = run_level_failedQcs["failedRunQc"]

    if run_level_failedQcs.get("failedControlQc", ""):
        results["failedControlQc"] = run_level_failedQcs["failedControlQc"]
        
    for sample in results["samples"]:
        if sample["qc_status"] == PASS:
            results["Samples_Passed"] += 1
        else:
            results["Samples_Failed"] += 1
        
    return results 

def grepInDebug(error, debug_path):
    cmd="/bin/grep -a -B4 -A16 \""+ error + "\" "+ debug_path 
    result = ""
    try:
        result=subprocess.check_output(cmd,shell=True).decode()
    except:
        pass
    return result

def checkDebugLog(data, archive_path):
    DEBUG_ERROR_KEYWORDS = ["PCR lid clamping failure"]
    DebugErrors={}

    id="PCR lid clamping failure"
    DebugErrors[id]={"errorReason":"PCR lid failed to close",
                     "evidence":["Experiment Errors", "/test_results/Experiment_Errors/results.html"],
                   "NextSteps":["Check PCR lid OPTO connections J14 on sample prep board"]}

    data["DebugErrors"]=False
    data["DebugErrorInfo"]=[]
    data["DebugErrorNextSteps"]=[]
    
    errors = []
    found = False


    debug_path = get_debug_path(archive_path)
    if not debug_path:
        logger.warn("No debug file found")
        return
    

    
    for key in DEBUG_ERROR_KEYWORDS:
        result=grepInDebug(key, debug_path)
        if not result == "":
            errors.append(key)
            found = True

        
    if found:
        data["DebugErrors"] = True
        for error in errors:
            for idx in DebugErrors:
                if idx in error:
                    #logger.warn("adding error {} for {}".format(error, idx))
                    data["DebugErrorInfo"].append(DebugErrors[idx]["errorReason"])
                    data["DebugErrorNextSteps"].append(DebugErrors[idx]["NextSteps"])
                    break
                
    # # check for errors that might not make it to explog
    # if data["RunAborted"]==False:
    #     for idx in AbortedChecks:
    #         result=grepInDebug(idx, debug_path)
    #         if not result == "":
    #             data["DebugErrorInfo"].append(AbortedChecks[idx]["errorReason"])
    #             data["DebugErrorNextSteps"].append(AbortedChecks[idx]["NextSteps"])

    return 
   

def checkSequencing(data, archive_path, output_path):
    
    lanes=0
    if data["explog"]["LanesActive1"] == "yes":
        lanes+=1
    if data["explog"]["LanesActive2"] == "yes":
        lanes+=1
    if data["explog"]["LanesActive3"] == "yes":
        lanes+=1
    if data["explog"]["LanesActive4"] == "yes":
        lanes+=1
    
    upperAvgLimit=8192+400
    lowerAvgLimit=8192-400
    avgDiffLimit=160
    lastAvg=0
    averageDoneOnce=False

    upperDSSLimit=3600
    lowerDSSLimit=1200
    dssDoneOnce=False
    
    upperDpfLimit=98
    diskDoneOnce=False
    
    upperFRLimit=(48+5)*lanes
    lowerFRLimit=(48-5)*lanes
    minFRLimit=5
    frDoneOnce=False
    
    upperFTempLimit=28
    lowerFTempLimit=20
    ftempDoneOnce=False
    
    upperVrefLimit=1.8
    lowerVrefLimit=1.0
    vrefDoneOnce=False
    
    rc=""
    for lineu in data["explog"]["ExperimentInfoLog"]:
        line=str(lineu)
        if len(line) > 0 and "acq_" in line:
            acq = int(line.split("acq_")[1].split(".dat")[0])
            # this is a experiment flow
            try:
                if not vrefDoneOnce:
                    vrefTxt=line.split("Vref=")[1] #.split(" ")[0])
                    try:
                        vref = float(vrefTxt)
                        if acq > 0:
                            if vref > upperVrefLimit or vref < lowerVrefLimit:
                                rc+= "Reference voltage is not within range  %f <= %f <= %f acq %d\n"%(lowerVrefLimit,vref,upperVrefLimit,acq)
                                vrefDoneOnce=True
                        else:
                            if vref > (upperVrefLimit+300) or vref < (lowerVrefLimit-300):
                                rc+= "Reference voltage is not within range  %f <= %f <= %f acq %d\n"%(lowerVrefLimit-300,vref,upperVrefLimit+300,acq)
                                vrefDoneOnce=True
                            
                    except:
                        logger.warn("exception with vref2 " + vrefTxt)                        
            except:
                logger.warn("exception with vref " + line)

            try:
                if not ftempDoneOnce:
                    ftempTxt=line.split("FTemp=")[1]
                    try:
                        ftemp=float(ftempTxt.split(" ")[0])
                        if ftemp > upperFTempLimit or ftemp < lowerFTempLimit:
                            rc+= "Flow Temperature is not within range  %f <= %f <= %f acq %d\n"%(lowerFTempLimit,ftemp,upperFTempLimit,acq)
                            ftempDoneOnce=True
                    except:
                        logger.warn("exception with ftemp2 " + ftempTxt)
            except:
                logger.warn("exception with ftemp " + line)

            try:
                if not frDoneOnce :
                    fr=float(line.split("FR=")[1].split(",")[0])
                    if fr < minFRLimit:
                        rc += "No Flow Detected. acq %d\n"%(acq)
                        frDoneOnce=True
                    elif fr > upperFRLimit or fr < lowerFRLimit:
                        rc += "Flow Rate is not within range  %f <= %f <= %f acq %d\n"%(lowerFRLimit,fr,upperFRLimit,acq)
                        frDoneOnce=True
            except:
                logger.warn("exception with flowrate " + line)

            try:
                if not averageDoneOnce:
                    averageTxt=line.split("avg=")[1]
                    try:
                        average=float(averageTxt.split(" ")[0])
                        if acq > 0:
                            if average > upperAvgLimit or average < lowerAvgLimit:
                                rc += "array average is not within range  %.0f <= %.0f <= %.0f acq %d\n"%(lowerAvgLimit,average,upperAvgLimit,acq)
                                averageDoneOnce=True
                            elif acq > 2 and lastAvg > 0 and abs(average - lastAvg) > avgDiffLimit:
                                rc += "array average difference %.0f > %.0f acq %d\n"%(abs(average-lastAvg),avgDiffLimit,acq)
                                averageDoneOnce=True
                            lastAvg=average
                    except:
                        logger.warn("exception with array average2 " + averageTxt)
                        
            except:
                logger.warn("exception with array average")

                    
            try:
                if not dssDoneOnce:
                    dss=float(line.split("dac_start_sig=")[1].split(" ")[0])
                    if dss > upperDSSLimit or dss < lowerDSSLimit:
                        rc += "dac_start_sig is not within range  %.0f <= %.0f <= %.0f acq %d\n"%(lowerDSSLimit,dss,upperDSSLimit,acq)
                        dssDoneOnce=True
            except:
                logger.warn("exception with dss")
                        
            try:
                if not diskDoneOnce:
                    dpf=float(line.split("diskPerFree=")[1].split(" ")[0])
                    if dpf > upperDpfLimit:
                        rc += "Disks are full acq %d\n"%(acq)
                        diskDoneOnce=True
            except:
                logger.warn("exception with diskPer")
             
    # lane=2
    # rc += image_tests.test_rawTrace(archive_path, output_path)
    # imgArg=archive_path+"/rawTrace/plots_lane_"+str(lane)+"/stepSize.middle.bead.png"
    # rc += image_tests.NucStepSize_test(imgArg)
    for lane in range(1,5):
        if data["explog"]["LanesActive"+str(lane)] == "yes":    
            imgArg=archive_path+"/rawTrace/plots_lane_"+str(lane)+"/keyBkgSub.middle.json"
            BKQrc= image_tests.test_BKQ(imgArg)
            rc += BKQrc
            
            NSSrc = ""
            imgArg=archive_path+"/NucStepSpatialV2/results.json"
            NSSrc = image_tests.NucStepSize_test(imgArg,lane)
            rc += NSSrc
            if NSSrc != "" or BKQrc != "":
                break
    
    #     ValkWF_path =os.path.join(archive_path, "ValkyrieWorkflow")
    # if os.path.exists(ValkWF_path): 
    #     for filename in os.listdir(ValkWF_path):
    #         if ("deckImage_Before_Seq_3" in filename) and (".png" in filename):
    #             deck_image_path = os.path.join(ValkWF_path,filename)
    #             break
    #     if ".png" in deck_image_path:
    #         sample_plate_position_report = sample_plate_position(deck_image_path)
    #         if not sample_plate_position_report == "":
    #             return print_alert(sample_plate_position_report)
                

       
    if rc == "":
        rc="Passed"
    data["SeqStatus"]=rc
    return rc        

def FailedSampleLogic(data,summary):
    # here because everything else is ok...
    # first, check inline controls.
    #logger.warn("FailedSampleLogic")
    inlineControlRslt="Passed"
    for name in data["IC"]:
        if "nomatch" in name:
            continue
        item=data["IC"][name]
        if isinstance(item,dict) and "ratio" in item:
            foundInline="Failed"
            for ratio in item["ratio"]:
                if item["ratio"][ratio] and item["ratio"][ratio] != "NA" and float(item["ratio"][ratio]) > 1.0:
                    foundInline="Passed"
            summary["Next Steps"].append([name + ": Inline Controls " + foundInline])
            if foundInline=="Failed":
                inlineControlRslt="Failed"
                
    summary["Next Steps"].append(["Inline Controls " + inlineControlRslt])
                 
    #if inlineControlRslt == "Passed":
            
    
def checkVacLog(data, archive_path):
    data["ChipCouplerFail"]=0
    data["ChipCouplerFail1"]=0
    data["ChipCouplerFail2"]=0
    data["ChipCouplerFail3"]=0
    data["ChipCouplerFail4"]=0
    filename=os.path.join(archive_path, "CSA/vacuum_log.csv")
    if os.path.exists(filename):
        with open(filename, "rb") as fp:
            info_rows = list(csv.reader(fp, delimiter=","))
            for row in info_rows:
                use=False
                lane="0"
                for col in row:
                    if "TEMPLATE: PostTemplating SDS Wash " in col:
                        use=True
                        lane=col.split("TEMPLATE: PostTemplating SDS Wash ")[1]
                if use:
                    Amp=0
                    Duty=0
                    
                    for colNum in range(0,len(row)):
                        if row[colNum] == "AmplitudeOfOscillation":
                            Amp=float(row[colNum+1])
                        elif row[colNum] == "PumpDutyCycle":
                            Duty=float(row[colNum+1])
                    if Amp > 0 and Duty > 0 and lane != "0":
                        if Amp < 0.2 and Duty > 15:
                            data["ChipCouplerFail"] = 1
                            data["ChipCouplerFail"+lane] = 1
                    else:
                        logger.warn("failed to get values " + row)


def checkValkWf(data, archive_path):
    data["pipWaterWellFail0"]=0
    data["pipWaterWellFail1"]=0
    data["pipInCouplerFail0"]=0
    data["pipInCouplerFail1"]=0
    data["VacFail0"]=0
    data["VacFail1"]=0
    data["tipPickupErrors_0"]=0
    data["tipPickupErrors_1"]=0
    data["pipErr52_0"]=0
    data["pipErr52_1"]=0
    data["bottomFail0"]=0
    data["bottomFail1"]=0
    data["ClogFail"]=0
    
    vwfPath=os.path.join(archive_path, "ValkyrieWorkflow/results.json")
    if os.path.exists(vwfPath):
        with open(vwfPath,"r") as fp:
            data["vwfPlugin"] = json.load(fp)
            
        if not "vacLog" in data["vwfPlugin"]:
            # pre-6.6 
            data["pipWaterWellFail0"] = data["vwfPlugin"]["pipPresTest"]["waterWell_fail"]["p1_count"] #checkPipPressure(pipPath,-70,0)
            data["pipWaterWellFail1"] = data["vwfPlugin"]["pipPresTest"]["waterWell_fail"]["p2_count"] #checkPipPressure(pipPath,-70,1)
            
            data["pipInCouplerFail0"] = data["vwfPlugin"]["pipPresTest"]["inCoupler_fail"]["p1_count"] #checkPipPressure(pipPath,-550,0)
            data["pipInCouplerFail1"] = data["vwfPlugin"]["pipPresTest"]["inCoupler_fail"]["p2_count"] #checkPipPressure(pipPath,-550,1)
            
            data["VacFail0"] = data["vwfPlugin"]["pipPresTest"]["vacTest_fail"]["p1_count"] #checkVacuumPressure(vacPath,-5.5,0)
            data["VacFail1"] = data["vwfPlugin"]["pipPresTest"]["vacTest_fail"]["p1_count"] #checkVacuumPressure(vacPath,-5.5,1)
            
        else:
            # 6.6 and higher
            if "bottomlog" in data["vwfPlugin"] and "missed_bottom_p1_count" in data["vwfPlugin"]["bottomlog"]:
                data["bottomFail0"] = data["vwfPlugin"]["bottomlog"]["missed_bottom_p1_count"]
                data["bottomFail1"] = data["vwfPlugin"]["bottomlog"]["missed_bottom_p2_count"]
            
            if "er52" in  data["vwfPlugin"] and "pipette_1" in data["vwfPlugin"]["er52"]:
                data["pipErr52_0"] = data["vwfPlugin"]["er52"]["pipette_1"]
                data["pipErr52_1"] = data["vwfPlugin"]["er52"]["pipette_2"]
            
            if "tip_pickup_errors" in data["vwfPlugin"] and "p1" in data["vwfPlugin"]["tip_pickup_errors"] and "struggle_count" in data["vwfPlugin"]["tip_pickup_errors"]["p1"]:
                data["tipPickupErrors_0"] = data["vwfPlugin"]["tip_pickup_errors"]["p1"]["struggle_count"] + data["vwfPlugin"]["tip_pickup_errors"]["p1"]["unable_count"] 
                data["tipPickupErrors_1"] = data["vwfPlugin"]["tip_pickup_errors"]["p2"]["struggle_count"] + data["vwfPlugin"]["tip_pickup_errors"]["p2"]["unable_count"] 
            
            for lane in 0,1,2,3,4:
                laneData=data["vwfPlugin"]["vacLog"]["lane "+str(lane)]
        
                if "postLib_suspected_leaks_count" in laneData: 
#                and \
#                   "postLib_suspected_clogs_count" in laneData and \
#                   "suspected_leaks_count" in laneData and \
#                   "suspected_clogs_count" in laneData:
                    data["VacFail0"] += int(laneData["postLib_suspected_leaks_count"])
#                     + \
#                                        int(laneData["postLib_suspected_clogs_count"]) + \
#                                        int(laneData["suspected_leaks_count"]) + \
#                                        int(laneData["suspected_clogs_count"])
                    data["VacFail1"] = data["VacFail0"]
                if "postLib_suspected_clogs_count" in laneData: 
                    data["ClogFail"] += int(laneData["postLib_suspected_clogs_count"])

def checkRunAborted(data, archive_path):
    data["RunAborted"]=False
    data["runAbortedReason"]=""
    data["runAbortedNextSteps"]=[]
    for line in data["explog"]["ExperimentErrorLog"]:
        if "Critical: Aborted" in line:
            data["RunAborted"]=True
        else:
            for idx in AbortedChecks:
                if idx in line:
                    data["runAbortedReason"]=AbortedChecks[idx]["errorReason"]
                    data["runAbortedNextSteps"]= AbortedChecks[idx]["NextSteps"]
                    data["evidence"]=AbortedChecks[idx]["evidence"]
                    break
                        
    if data["RunAborted"] and data["runAbortedReason"]=="":
        # run aborted, but the reason is not known.
        # check for a generic exception
        cmd="/bin/grep -a -B4 -A16 Traceback "+archive_path+"/CSA/debug | tail -n 20"
        try:
            result=subprocess.check_output(cmd,shell=True).decode()
            #logger.warn("got back : "+result)
            if not result == "":
                data["runAbortedReason"]="Generic Exception"
                data["evidence"]=["Experiment Errors", "/test_results/Experiment_Errors/results.html"]
                for ln in result.splitlines():
                    data["runAbortedNextSteps"].append(ln)
        except:
            logger.warn("exception trying to get Generic Aborted Reason from debug")
            result=""
            
def decisionLogic(data, mock):

    summary=OrderedDict()
    summary["Issues Detected"]=[]
    summary["Next Steps"]=[]
    FailReason=""
    if data["RunAborted"]:
        FailReason=data["runAbortedReason"]
        summary["Issues Detected"].append([FailReason])
        for line in data["runAbortedNextSteps"]:
            summary["Next Steps"].append([line])
    elif "No Flow Detected" in data["SeqStatus"]:
        FailReason = "Fluidic Issue Detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in data["SeqStatus"].splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["No Flow rate detected. The most likely cause is a crimped W2 bottle seal."])        
        summary["Next Steps"].append(["Check W2 bottle seal."])        
        summary["Next Steps"].append(["If W2 bottle seal looks ok, Run the Fluidics factory test. retry the run."])
        data["evidence"]=["Auto Cal", "/autoCal/autoCal.html"]

    elif "Flow Rate is not within range" in data["SeqStatus"]:
        FailReason = "Fluidic Issue Detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in data["SeqStatus"].splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["Flow rate not correct. The most likely cause is a clog."])        
        summary["Next Steps"].append(["Run the Fluidics factory test. retry the run."])
        data["evidence"]=["Auto Cal", "/autoCal/autoCal.html"]
        
    elif "array average is not within range" in data["SeqStatus"] or "array average difference" in data["SeqStatus"] or "RawTrace:" in data["SeqStatus"]:
        FailReason = "Electrical Issue Detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in data["SeqStatus"].splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["The most likely cause is a salt bridge on the squid."])
        summary["Next Steps"].append(["Wipe salt residue from the squid and retry the run."])
        if "RawTrace: Lane 1" in data["SeqStatus"]:
            data["evidence"]=["rawTrace", "/rawTrace/html_plots_lane_1/region.middle.html"]
        elif "RawTrace: Lane 2" in data["SeqStatus"]:
            data["evidence"]=["rawTrace", "/rawTrace/html_plots_lane_2/region.middle.html"]
        elif "RawTrace: Lane 3" in data["SeqStatus"]:
            data["evidence"]=["rawTrace", "/rawTrace/html_plots_lane_3/region.middle.html"]
        elif "RawTrace: Lane 4" in data["SeqStatus"]:
            data["evidence"]=["rawTrace", "/rawTrace/html_plots_lane_4/region.middle.html"]
        else:
            data["evidence"]=["Auto Cal", "/autoCal/autoCal.html"]
        
    elif not mock and (data["bottomFail0"] > 0 or data["bottomFail1"] > 0):
        FailReason = "Bottom find Issue Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely causes are pipette malfunction or bad deck calibration."])
        summary["Next Steps"].append(["Check Tip adapters."])
        summary["Next Steps"].append(["re-run deck calibration."])
        summary["Next Steps"].append(["Run the pipette factory test."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
        
    elif not mock and (data["tipPickupErrors_0"] > 0 or data["tipPickupErrors_1"] > 0):
        FailReason = "Tip Pickup Issue Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely causes are bad deck calibration, bad tip adapter, or mis-seated tips."])
        summary["Next Steps"].append(["Check tip rack for mis-seated tips."])
        summary["Next Steps"].append(["Check Tip adapters."])
        summary["Next Steps"].append(["re-run deck calibration."])
        summary["Next Steps"].append(["Run the pipette factory test."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
        
    elif not mock and (data["VacFail0"] > 0 or data["VacFail1"] > 0):
        FailReason = "Vacuum Issue Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a blocked vacuum."])
        summary["Next Steps"].append(["Run the vacuum factory test."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
    elif not mock and (data["ClogFail"] > 0):
        FailReason = "Clog Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is the chip coupler."])
        summary["Next Steps"].append(["Check the chip coupler alignment."])
        summary["Next Steps"].append(["Run the chip coupler factory test."])
        summary["Next Steps"].append(["Run the vacuum factory test."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]   
    elif not mock and (data["pipInCouplerFail0"] > 0 and data["pipInCouplerFail1"] > 0):
        FailReason = "Pipette 1 and 2 Issues Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a bad pipette."])
        summary["Next Steps"].append(["Replace Pipettes 1,2 and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
        
    elif not mock and (data["pipInCouplerFail0"] or data["pipErr52_0"] > 0):
        FailReason = "Pipette 1 Issue Detected   Pipette 2 ok"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a bad pipette 1."])
        summary["Next Steps"].append(["Replace Pipette 1 and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]

    elif not mock and (data["pipInCouplerFail1"] > 0 or data["pipErr52_1"]):
        FailReason = "Pipette 2 Issues Detected   Pipette1 ok"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a bad pipette 2."])
        summary["Next Steps"].append(["Replace Pipette 2 and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
    
    elif "Background-subtracted key traces test failed" in data["SeqStatus"]:
        FailReason = "Swapped Nuc detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in data["SeqStatus"].splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["Nuc swap detected."])        
        summary["Next Steps"].append(["Replace the cartridge and retry the run."])
        data["evidence"]=["rawTrace", "/rawTrace/rawTrace_lane_3.html"]
        
    elif "Nuc swap or missing detected" in data["SeqStatus"]:
        FailReason = "Swapped or Missing Nuc detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in data["SeqStatus"].splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["Swapped or missing NUC detected."])        
        summary["Next Steps"].append(["Replace the cartridge and retry the run."])
        data["evidence"]=["rawTrace", "/rawTrace/rawTrace_lane_3.html"]
        
    elif data["ChipCouplerFail"] > 0:
        FailReason = "Chip Coupler Issues Detected"
        summary["Issues Detected"].append([FailReason])
        for lane in range(1,5):
            if data["ChipCouplerFail"+str(lane)] > 0:
                summary["Next Steps"].append(["No resistance detected on TEMPLATE PostTemplating SDS Wash "+str(lane)])
        summary["Next Steps"].append(["The chip coupler is likely not making a good connection"])
        summary["Next Steps"].append(["The most likely cause is a bad Chip Coupler"])
        summary["Next Steps"].append(["Replace the chip coupler and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/Workflow_VacuumLog.html"]
        
    elif data["DebugErrors"]:
        FailReason="Debug log errors"
        data["evidence"]=["Experiment Errors", "/test_results/Experiment_Errors/results.html"]
        for i in range(len(data["DebugErrorInfo"])):
            error = data["DebugErrorInfo"][i]
            summary["Issues Detected"].append([error])
            for line in data["DebugErrorNextSteps"][i]:
                summary["Next Steps"].append([line])
    elif data["qc"]["Samples_Failed"] > 0:
        FailReason="Failed Sample detected"        
        FailedSampleLogic(data,summary)  
    else:
        if mock:
            FailReason="Mock Run Passed"
        else:
            FailReason = "Problem not detected."
        summary["Issues Detected"].append([FailReason])
    
    if mock and FailReason != "Mock Run Passed":
        FailReason="Mock Run Failed"
    
    data["FailReason"]=FailReason
    return summary

def execute(archive_path, output_path, archive_type):
        
    data={}
    #try:
    expPath=archive_path+"/CSA/explog_final.json"
    if not os.path.exists(expPath):
        expPath=archive_path+"/explog.json"
    with open(expPath, "r") as fp:
        data["explog"] = json.load(fp)
    #except:
    #    print_info("failed to get explog_final.json")

    data["qc"] = GetQCMetrics(archive_path, output_path, archive_type)
    data["qc"]["failedControlQC"]=0
    data["evidence"]=[]
    
    rtp = os.path.join(archive_path, "True_loading")
    #try:
    with open(os.path.join(rtp+"/results.json"), "r") as fp:
        data["loading"] = json.load(fp)
    #except:
    #    print_info("failed to get loading metrics")
    
    
    InlinePath = os.path.join(archive_path, "CSA/outputs/BaseCallingActor-00/")
    #try:
    if os.path.exists(InlinePath+"/inline_control_stats.json"):
        with open(os.path.join(InlinePath+"/inline_control_stats.json"), "r") as fp:
            data["IC"] = json.load(fp)
    else:
        data["IC"]={}
    data["IC"]["FailedReadRatios"]=0
    #except:
    #    print_info("failed to get inline controls")

    mock=("mock" in data["explog"]["Experiment Name"] or "Mock" in data["explog"]["Experiment Name"] or data["explog"]["Flows"]==100)
    
    checkValkWf(data, archive_path)      
    checkVacLog(data, archive_path)  
    checkRunAborted(data, archive_path)
    checkDebugLog(data,archive_path)
    checkSequencing(data,archive_path, output_path)

    status="Passed"
    if data["IC"]["FailedReadRatios"] > 0:   # read ratio's < 1 problematic
        status="Failed"
    if data["qc"]["failedControlQC"] > 0:   # or total_valid_reads < 10000
        status="Failed"
    
    summary=decisionLogic(data,mock)

    suffix_to_remove = '/test_results/Genexus_TroubleShooter'
    support=OrderedDict()
    if len(data["evidence"]) > 0:
        output_root = output_path[:-len(suffix_to_remove)]
        output_link = settings.MEDIA_URL + os.path.relpath(output_root, settings.MEDIA_ROOT) + data["evidence"][1]
    
        support["Supporting Data"]=[]
    
        row = {}
        row['name'] = data["evidence"][0]
        row['url'] = output_link
        support["Supporting Data"].append(row)
        # copy the image files for the supporting web page to our output_path
        img_dir = (data["evidence"][1].rsplit("/", 1))[0]
        # remove the links for files we are about to generate.  Otherwise we will just corrupt the evidence directory
        os.system("ln -s "+archive_path+ img_dir + "/* "+output_path+"/; rm "+output_path+"/results.html "+output_path+"/main.json "+output_path+"/output.json")
        if "rawTrace" in img_dir:
            os.system("ln -s "+archive_path+ img_dir.replace("/html_","/") + " "+output_path+"/../") 

    with open(os.path.join(output_path+"/output.json"), "w") as fp:
        json.dump(data,fp)
        
    logger.warn("output_path={} dirname={}".format(output_path,os.path.dirname(os.path.realpath(__file__))))

    write_results_from_template(
        {"other_runDetails": summary,
         "support": support},
        output_path,
        os.path.dirname(os.path.realpath(__file__))
        )
    
    if data["FailReason"] == "Problem not detected.":
        rc=print_info(data["FailReason"])
    elif data["FailReason"] == "Mock Run Passed":
        rc=print_ok(data["FailReason"])
    else:
        rc=print_alert("       <b><u>***{}***</u></b>    See Results for more details".format(data["FailReason"]))
        
    return rc
