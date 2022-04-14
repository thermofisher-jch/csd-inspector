#!/usr/bin/env python
import os
import time
import csv
import fnmatch
import copy
import json
import logging
from reports.diagnostics.common.inspector_utils import (
    read_explog,
    print_info,
    print_alert,
    print_ok,
    write_results_from_template,
)
from django.conf import settings
from collections import OrderedDict
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


def get_other_details(rows):
    other_headers = [
        "Software Version Details",
        "Sample Details",
        "Library Details",
        "Run Details",
        "Assay Details",
        "Reagent Information",
        "Consumable Information",
        "Analysis",
        "Instrument Summary",
        "Evaluation Metrics",
    ]
    other_runDetails = {}
    tempHeader = None
    for row in rows:
        if len(row):
            if any(header in row[0] for header in other_headers):
                tempHeader = row[0]
                if "Evaluation Metrics" not in tempHeader:
                    other_runDetails[tempHeader] = []
                continue
            if (
                "Evaluation Metrics" not in tempHeader
                and tempHeader in other_runDetails
            ):
                other_runDetails[tempHeader].append(row)

    return other_runDetails


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


def transform_data_for_display(sample_data):
    """
    qc_data:
        list_sections:
            section_name -> h3
            rows -> values
    """
    sections = sample_data["metrics"].keys()
    metrics_names = sample_data["keys"]
    sections_data = []
    for sect in sections:
        metrics = sample_data["metrics"][sect]
        metrics_values = []
        for m in metrics:
            metrics_values.append([m[k] for k in metrics_names])
        sections_data.append(metrics_values)

    return metrics_names, zip(sections, sections_data)

def checkPipPressure(basename,limit,pip):
    rc=0
    for lane in [1,2,3,4]:
        for attempt in [0,1]:
            filename = '{}_lane{}_try{}_PIP{}.csv'.format(basename,lane,attempt,pip)
            if os.path.exists(filename):
                try:
                    p=[]
                    with open(filename) as csv_file:
                        csv_reader = csv.reader(csv_file, delimiter=',')
                        list_csv = list(csv_reader)
                        for i,line in enumerate(list_csv):
                            p.append(float(line[0]))
                    if p[-1] > limit:
                        rc+=1
                except:
                    logger.warn("exception happened in checkPipPressure")
                    pass
            #else:
            #    logger.warn("did not find " + filename)
       
    return rc

def checkVacuumPressure(basename,limit,pip):
    rc=0
    for lane in [1,2,3,4]:
        filename = '{}Vacuum_PressureDataLANE{}_PIP{}.csv'.format(basename,lane,pip+1)
        if os.path.exists(filename):
            try:
                p=[]
                with open(filename) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    list_csv = list(csv_reader)
                    for i,line in enumerate(list_csv):
                        p.append(float(line[5]))
                if p[-1] > limit:
                    rc+=1
            except:
                logger.warn("exception happened in checkVacuumPressure")
                pass
        else:
            logger.warn("did not find " + filename)
       
    return rc
    
def GetQCMetrics(archive_path, output_path, archive_type):    

    results = {"num_failed_samples": 0, "Samples_Passed": 0, "Samples_Failed": 0, "failedRunQc": 0, "failedControlQc": 0, "samples" : []}
    info_per_sample = []
    failed_samples = []
    run_level_runQcdata = []
    run_level_controlQcdata = []
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
                        metrics_names, qc_data = transform_data_for_display(sample_data)
                        _, failed_qc_data = transform_data_for_display(failed_data)
                        _, runQc_data = transform_data_for_display(runQc_data)
                        _, controlQc_data = transform_data_for_display(controlQc_data)
        
                        info_per_sample.append([sample_name, info_rows, metrics_names, qc_data])
                        run_level_runQcdata.append([metrics_names, runQc_data])
                        run_level_controlQcdata.append([metrics_names, controlQc_data])
                        if failed_data["qc_status"] == FAIL:
                            failed_samples.append(
                                [sample_name, None, metrics_names, failed_qc_data]
                            )
        
                        results["samples"].append(sample_data)
    except:
        logger.warn("Exception in GetQCMetrics")
                    

    info_per_sample.sort(key=lambda x: x[0])

    
    if run_level_failedQcs.get("failedRunQc", ""):
        results["failedRunQc"] = run_level_failedQcs["failedRunQc"]

    if run_level_failedQcs.get("failedControlQc", ""):
        results["failedControlQc"] = run_level_failedQcs["failedControlQc"]
        
    for sample in results["samples"]:
        if sample["qc_status"] == PASS:
            results["Samples_Passed"] += 1
        else:
            results["Samples_Failed"] += 1

    write_results_from_template(
        {
            "info_per_sample": info_per_sample,
            "failed_samples": failed_samples,
            "run_level_data": [[run_level_runQcdata[0]], [run_level_controlQcdata[0]]],
            "other_runDetails": get_other_details(infoRowsForOtherDetails),
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )
        
    return results    

def checkSequencing(data):
    
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
                    
                
                
            
#    for line in data["explog"]["ExperimentErrorLog"]:
#        if not "The instrument must be serviced" in line:
#            rc+=line+"\n"
    
    return rc        


def checkValkWf(data, archive_path):
    data["pipWaterWellFail0"]=0
    data["pipWaterWellFail1"]=0
    data["pipInCouplerFail0"]=0
    data["pipInCouplerFail1"]=0
    data["VacFail0"]=0
    data["VacFail1"]=0
    vwfPath=os.path.join(archive_path, "ValkyrieWorkflow/results.json")
    if os.path.exists(vwfPath):
        with open(vwfPath,"r") as fp:
            data["vwfPlugin"] = json.load(fp)
            
        if not "vacLog" in data["vwfPlugin"]:
            # 6.6 and forward compatible
            data["pipWaterWellFail0"] = data["vwfPlugin"]["pipPresTest"]["waterWell_fail"]["p1_count"] #checkPipPressure(pipPath,-70,0)
            data["pipWaterWellFail1"] = data["vwfPlugin"]["pipPresTest"]["waterWell_fail"]["p2_count"] #checkPipPressure(pipPath,-70,1)
            
            data["pipInCouplerFail0"] = data["vwfPlugin"]["pipPresTest"]["inCoupler_fail"]["p1_count"] #checkPipPressure(pipPath,-550,0)
            data["pipInCouplerFail1"] = data["vwfPlugin"]["pipPresTest"]["inCoupler_fail"]["p2_count"] #checkPipPressure(pipPath,-550,1)
            
            data["VacFail0"] = data["vwfPlugin"]["pipPresTest"]["vacTest_fail"]["p1_count"] #checkVacuumPressure(vacPath,-5.5,0)
            data["VacFail1"] = data["vwfPlugin"]["pipPresTest"]["vacTest_fail"]["p1_count"] #checkVacuumPressure(vacPath,-5.5,1)
        else:
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
                # else:
                #     data["VacFail0"] = 100

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
        # cmd=["/bin/grep","TestLine FluidicsManifold failed to Close.  Check opto fluidMan_close",archive_path + "/CSA/debug"]
        # try:
        #     result=subprocess.check_output(cmd).decode()
        #     logger.warn("got back : "+result)
        # except:
        #     logger.warn("exception trying to get Aborted Reason from debug")
        #     result=""
        # if "Check opto" in result:
        #     data["runAbortedReason"]="FluidicsManifold failed to Close."
        #     data["runAbortedNextSteps"].append("Run the Chip Clamp factory test")
        #     data["runAbortedNextSteps"].append("Check opto fluidMan_close")
        #     data["evidence"]=["Experiment Errors", "/test_results/Experiment_Errors/results.html"]
        # else:
        if 1:
            # check for a generic exception
            cmd="/bin/grep -a -B4 -A16 Traceback "+archive_path+"/CSA/debug | tail -n 20"
            try:
                result=subprocess.check_output(cmd,shell=True).decode()
                logger.warn("got back : "+result)
                if not result == "":
                    data["runAbortedReason"]="Generic Exception"
                    data["evidence"]=["Experiment Errors", "/test_results/Experiment_Errors/results.html"]
                    for ln in result.splitlines():
                        data["runAbortedNextSteps"].append(ln)
            except:
                logger.warn("exception trying to get Generic Aborted Reason from debug")
                result=""
            


def execute(archive_path, output_path, archive_type):
        
    data={}
    data["qc"] = GetQCMetrics(archive_path, output_path, archive_type)
    data["qc"]["failedControlQC"]=0
    data["evidence"]=[]
    
    #try:
    expPath=archive_path+"/CSA/explog_final.json"
    if not os.path.exists(expPath):
        expPath=archive_path+"/explog.json"
    with open(expPath, "r") as fp:
        data["explog"] = json.load(fp)
    #except:
    #    print_info("failed to get explog_final.json")
    
    
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
    
    checkValkWf(data, archive_path)        
    checkRunAborted(data, archive_path)
    

    data["ComponentStatus"]=[]

    status="Passed"
    if data["IC"]["FailedReadRatios"] > 0:   # read ratio's < 1 problematic
        status="Failed"
    data["ComponentStatus"].append(["Library Prep",status])
    
    status="Passed"
    if data["qc"]["failedControlQC"] > 0:   # or total_valid_reads < 10000
        status="Failed"
    data["ComponentStatus"].append(["Templating",status])
    
    SeqStatus=checkSequencing(data)
    if SeqStatus == "":
        SeqStatus="Passed"
    data["ComponentStatus"].append(["Sequencing",SeqStatus])
    
    data["ComponentStatus"].append(["Post Run Clean","Passed"])

    summary=OrderedDict()
    summary["Issues Detected"]=[]
    summary["Next Steps"]=[]

    FailReason=""
    if data["RunAborted"]:
        FailReason=data["runAbortedReason"]
        summary["Issues Detected"].append([FailReason])
        for line in data["runAbortedNextSteps"]:
            summary["Next Steps"].append([line])
    elif "No Flow Detected" in SeqStatus:
        FailReason = "Fluidic Issue Detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in SeqStatus.splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["No Flow rate detected. The most likely cause is a crimped W2 bottle seal."])        
        summary["Next Steps"].append(["Check W2 bottle seal."])        
        summary["Next Steps"].append(["If W2 bottle seal looks ok, Run the Fluidics factory test. retry the run."])
        data["evidence"]=["Auto Cal", "/autoCal/autoCal.html"]

    elif "Flow Rate is not within range" in SeqStatus:
        FailReason = "Fluidic Issue Detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in SeqStatus.splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["Flow rate not correct. The most likely cause is a clog."])        
        summary["Next Steps"].append(["Run the Fluidics factory test. retry the run."])
        data["evidence"]=["Auto Cal", "/autoCal/autoCal.html"]
        
    elif "array average is not within range" in SeqStatus or "array average difference" in SeqStatus:
        FailReason = "Electrical Issue Detected"
        summary["Issues Detected"].append([FailReason])
        for newReason in SeqStatus.splitlines():
            summary["Issues Detected"].append([newReason])        
        summary["Next Steps"].append(["The most likely cause is a salt bridge on the squid."])
        summary["Next Steps"].append(["Wipe salt residue from the squid and retry the run."])
        data["evidence"]=["Auto Cal", "/autoCal/autoCal.html"]
        
    elif (data["VacFail0"] > 0 or data["VacFail1"] > 0):
        FailReason = "Vacuum Issue Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a blocked vacuum."])
        summary["Next Steps"].append(["Run the vacuum factory test."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
        
    elif data["pipInCouplerFail0"] > 0 and data["pipInCouplerFail1"] > 0:
        FailReason = "Pipette 1 and 2 Issues Detected"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a bad pipette."])
        summary["Next Steps"].append(["Replace Pipettes 1,2 and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
        
    elif data["pipInCouplerFail0"] > 0:
        FailReason = "Pipette 1 Issue Detected   Pipette 2 ok"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a bad pipette 1."])
        summary["Next Steps"].append(["Replace Pipette 1 and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]

    elif data["pipInCouplerFail1"] > 0:
        FailReason = "Pipette 2 Issues Detected   Pipette1 ok"
        summary["Issues Detected"].append([FailReason])
        summary["Next Steps"].append(["The most likely cause is a bad pipette 2."])
        summary["Next Steps"].append(["Replace Pipette 2 and retry the run."])
        data["evidence"]=["Genexus Workflow", "/ValkyrieWorkflow/ValkyrieWorkflow_block.html"]
    else:
        FailReason = "Problem not detected."
        summary["Issues Detected"].append([FailReason])
        

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
        os.system("ln -s "+archive_path+ img_dir + "/* "+output_path+"/")

    with open(os.path.join(output_path+"/output.json"), "w") as fp:
        json.dump(data,fp)
    
    
    #if not FailReason == "Problem not detected.":
    write_results_from_template(
        {"other_runDetails": summary,
         "support": support},
        output_path,
        os.path.dirname(os.path.realpath(__file__))
        )

    #time.sleep(120)
        
    # with open(os.path.join(output_path+"/summary.json"), "w") as fp:
    #     json.dump(summary,fp)        
    
    if FailReason == "Problem not detected.":
#        message = " <a target='_blank' href='{}'>dbg_output</a> {}".format(
#            output_link,FailReason)
        rc=print_info(FailReason)
    else:
        # message = " <a target='_blank' href='{}'>dbg_output</a> <b>       <u>***{}***</u>   </b> See Results for more details".format(
        #     output_link,FailReason)
        rc=print_alert("       <b><u>***{}***</u></b>    See Results for more details".format(FailReason))
        
    return rc
