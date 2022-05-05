# -*- coding: utf-8 -*-
# !/usr/bin/env python
import os
import csv
import fnmatch
import copy
import json
import logging
import subprocess
from collections import OrderedDict
from reports.diagnostics.common.inspector_utils import (
    read_explog,
    print_info,
    print_alert,
    print_ok,
    write_results_from_template,
)

logger = logging.getLogger(__name__)

def execute(archive_path, output_path, archive_type):
    quant_sumF=os.path.join(output_path, "Quant_summary.csv")
    quant_reagF=os.path.join(output_path, "Quant_reagent.csv")
    quant_samplesF=os.path.join(output_path, "Quant_samples.csv")

    cmd="find " + archive_path + " -name Quant_summary.csv | head -n 1"
    try:
        filename=subprocess.check_output(cmd,shell=True).decode()
    except:
        filename=""
    #logger.warn("got back : "+filename)

    if filename == "":
        rc=print_info("NA")
    else:
        cmd="grep 'Well Name' " + filename.strip()
        result = ""
        try:
            result=subprocess.check_output(cmd,shell=True).decode()
        except:
            pass
        
        WN="Well Name"
        if result == "":
            WN="Sample Name"
        
        cmd="sed '/Plate Name/q' " + filename.strip() + " | grep -v 'Plate Name' | sed 's/\"//g' > "+quant_sumF
        os.system(cmd)
        #logger.warn(cmd)
        cmd="sed -n '/Plate Name/,/" + WN + "/p' " + filename.strip() + " | grep -v '"+WN+"' | sed 's/\"//g' > "+quant_reagF
        os.system(cmd)
        #logger.warn(cmd)
        cmd="sed -n '/"+WN+"/,$p' " + filename.strip() + " | sed 's/\"//g' > "+quant_samplesF
        os.system(cmd)
        #logger.warn(cmd)
        
        summary=OrderedDict()
        support=OrderedDict()

        with open(quant_sumF, "rb") as fp:
            summary["Summary"] = list(csv.reader(fp, delimiter=","))
        #logger.warn(summary)

        with open(quant_reagF, "rb") as fp:
            support["Reagent Lot"] = {}
            tmp = list(csv.reader(fp, delimiter=","))
            support["Reagent Lot"]["header"]=tmp[0]
            support["Reagent Lot"]["data"]=tmp[1:]
            smp=support["Reagent Lot"]
            for i in range(len(smp["header"])):
                if smp["header"][i].strip() == "expiryDate":
                    smp["header"][i]="Expiration Date";
                    for j in range(len(smp["data"])):
                        if len(smp["data"][j]) > i and len(smp["data"][j][i]) == 7:
                            smp["data"][j][i]="20"+smp["data"][j][i][1]+smp["data"][j][i][2] + "-" + smp["data"][j][i][3]+smp["data"][j][i][4] + "-" + smp["data"][j][i][5] + smp["data"][j][i][6]
                    break
        #logger.warn(support)
            
        with open(quant_samplesF, "rb") as fp:
            support["Samples"] = {}
            tmp = list(csv.reader(fp, delimiter=","))
            #logger.warn(tmp)
            #logger.warn(tmp[1:])
            support["Samples"]["header"]=tmp[0]
            support["Samples"]["data"]=tmp[1:]
            
            
            smp=support["Samples"]
            #logger.warn(summary)
            for i in range(len(smp["header"])):
                #logger.warn("{}: ".format(i)+smp["header"][i])
                if smp["header"][i].strip() == "Concentration":
                    #logger.warn("{}: found match".format(i))
                    smp["header"][i]="Concentration ng/ul";
                    for j in range(len(smp["data"])):
                        #logger.warn("{}: {} {}".format(j,smp["data"][j][i],len(smp["data"][j][i])))
                        if len(smp["data"][j]) > i and len(smp["data"][j][i]) > 0:
                            smp["data"][j][i]="{:.02f}".format(float(smp["data"][j][i]))
                    break
        #logger.warn(support)
                

        write_results_from_template(
            {"other_runDetails": summary,
             "support": support},
            output_path,
            os.path.dirname(os.path.realpath(__file__))
            )
        rc=print_info("See results for details")
    return rc

if __name__ == "__main__":
    import os
    import sys
    from django import setup

    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    setup()
    archive_path_arg, output_path_arg, archive_type_arg = sys.argv[1:4]
    execute(archive_path_arg, output_path_arg, archive_type_arg)
