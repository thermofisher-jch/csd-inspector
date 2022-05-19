#!/usr/bin/env python

import json
import os
import re
import shutil
import sys
import logging

import numpy

from reports.diagnostics.common.inspector_utils import (
    write_results_from_template,
    print_info,
    print_alert,
    handle_exception,
)

logger = logging.getLogger(__name__)


def get_read_group_file_prefixes(datasets_basecaller_object):
    file_prefixes = {}
    for item in datasets_basecaller_object["datasets"]:
        for group in item["read_groups"]:
            file_prefixes[group] = item["file_prefix"]
    return file_prefixes


def get_read_groups(datasets_basecaller_object, barcode_to_nucleotide_types):
    def get_barcode_name(read_key, read_group):
        # "barcode_name" is not present, it can be combined barcode or no barcode
        if "barcode_name" not in read_group:
            if "." in read_key:
                # combined barcodes
                return read_key.split(".").pop()
            else:
                # a non-barcode rerun
                return u"No Barcode"
        return read_group.get("barcode_name")

    def shape_group_data(read_key, read_group):
        barcode_name = get_barcode_name(read_key=read_key, read_group=read_group)
        nucleotide_type = read_group.get("nucleotide_type", u"")
        if nucleotide_type == u"":
            nucleotide_type = barcode_to_nucleotide_types.get(
                barcode_name, nucleotide_type
            )
        return {
            "filtered": read_group.get("filtered", False) or "nomatch" in read_key,
            "sample_name": read_group.get("sample", "N/A"),
            "name": barcode_name,
            "end_barcode": read_group.get("end_barcode", {}).get("barcode_name", ""),
            "read_count": read_group.get("read_count", 0),
            "index": read_group.get("index", -1),
            "group": read_key,
            "nuc_type": nucleotide_type,
        }

    groups = [
        shape_group_data(key, value)
        for (key, value) in datasets_basecaller_object["read_groups"].iteritems()
    ]
    return sorted(groups, key=lambda k: k["index"])


def get_histogram_data(archive_path, barcode):
    if barcode == "No Barcode":
        barcode = "nomatch"
    ionstats_basecaller_path = os.path.join(
        archive_path,
        "CSA/outputs/BaseCallingActor-00/{}_rawlib.ionstats_basecaller.json".format(
            barcode
        ),
    )
    if os.path.exists(ionstats_basecaller_path):
        with open(ionstats_basecaller_path) as fp:
            ionstats_basecaller = json.load(fp)
            return list(enumerate(ionstats_basecaller["full"]["read_length_histogram"]))
    else:
        return []


def genexus_map_barcode_to_nucleotide_type(archive_path):
    library_type_re = re.compile("^Library Type,([^,]*),")
    barcode_id_re = re.compile("^Barcode Id,([^,]*),")
    barcodes_to_nucleotide_type = {}
    csa_root = os.path.join(archive_path, "CSA")
    for info_csv_path in {
        os.path.join(csa_root, x, "Info.csv")
        for x in os.listdir(csa_root)
        if os.path.exists(os.path.join(csa_root, x, "Info.csv"))
    }:
        with open(info_csv_path) as info_handle:
            next_expected = library_type_re
            next_line = info_handle.readline()
            next_nuc_type = None
            while next_line != "":
                next_match = next_expected.match(next_line)
                if next_match is not None:
                    if next_expected == library_type_re:
                        next_nuc_type = next_match.groups()[0].decode()
                        next_expected = barcode_id_re
                    else:
                        next_barcode_id = next_match.groups()[0].decode()
                        barcodes_to_nucleotide_type[next_barcode_id] = next_nuc_type
                        next_expected = library_type_re
                        next_nuc_type = None
                next_line = info_handle.readline()
    return barcodes_to_nucleotide_type


def execute(archive_path, output_path, archive_type):
    if archive_type == "Valkyrie":
        datasets_path = "CSA/outputs/BaseCallingActor-00/datasets_basecaller.json"
        barcodes_to_nucleotide_types = genexus_map_barcode_to_nucleotide_type(
            archive_path
        )
    else:
        datasets_path = "basecaller_results/datasets_basecaller.json"
        barcodes_to_nucleotide_types = {}

    if not os.path.exists(os.path.join(archive_path, datasets_path)):
        return print_alert("no basecaller info available.")

    with open(os.path.join(archive_path, datasets_path)) as datasets_file:
        datasets_object = json.load(datasets_file)

    groups = get_read_groups(datasets_object, barcodes_to_nucleotide_types)

    # get all of the filtered data sets
    total_reads = sum([float(x["read_count"]) for x in groups])
    filtered_data = [float(x["read_count"]) for x in groups if not x["filtered"]]
    mean = numpy.mean(filtered_data)
    min_read_cound = numpy.min(filtered_data) if filtered_data else 0
    std = numpy.std(filtered_data)

    histograms = []
    # group, sparkline_path, histogram_data, inline_control
    if archive_type == "Valkyrie":
        inline_controls_source_path = os.path.join(
            archive_path, "CSA/outputs/BaseCallingActor-00/inline_control_stats.json"
        )
        inline_controls_diag_path = os.path.join(
            output_path, "inline_control_stats.json"
        )
        try:
            # If a link exists from a previous execution, delete and re-create it.
            if os.path.exists(inline_controls_diag_path):
                os.unlink(inline_controls_diag_path)
            os.symlink(inline_controls_source_path, inline_controls_diag_path)
            inline_control_stats = True
        except OSError as exp:
            # Not a severe enough error to halt the report, but log it and prevent
            # rendering a broken link.
            logger.exception("Error linking inline_controls", exc_info=exp)
            inline_control_stats = False
            
        data={}
        data["inline"]={}
        try:
            with open(inline_controls_source_path, "r") as fp:
                data["inline"]=json.load(fp)
        except:
            pass
        
        histograms_first_pass = []
        sample_mapping = {}
        for group in groups:
            barcode_name = group["name"]
            src_image_path = os.path.join(
                archive_path,
                "CSA/outputs/BaseCallingActor-00/{}_rawlib.inline_control.png".format(
                    barcode_name
                ),
            )
            dst_image_path = os.path.join(
                output_path, "{}.inline_control.png".format(barcode_name)
            )

            if os.path.exists(src_image_path):
                # Copy to test dir
                shutil.copyfile(src_image_path, dst_image_path)
                inline_path = os.path.basename(dst_image_path)
            else:
                inline_path = None

            sample_name = group["sample_name"]
            if sample_name != "N/A":  # single barcode
                sample_mapping[barcode_name] = sample_name

            nameKey=barcode_name+"_rawlib.basecaller.bam"
            group["icvals"]=""
            try:
                inlineData=[""]*len(data["inline"][nameKey]["ratio"])
                if nameKey in data["inline"]: 
                    for key in data["inline"][nameKey]["ratio"]:     
                        keys=key.strip().split("/")
                        keysTxt="("+keys[0].strip() + ") "  + " / " "("+keys[1].strip() + ") "
                        inlineIndex=-1
                        if keys[1] == "ASC_Siz10:154-210":
                            keysTxt="100bp:"
                            inlineIndex=1
                        if keys[1] == "ASC_Siz10:687-902":
                            keysTxt="266bp:"
                            inlineIndex=4
                        if keys[1] == "ASC_Siz10:473-596":
                            keysTxt="178bp:"
                            inlineIndex=3
                        if keys[1] == "ASC_Siz10:996-1315":
                            keysTxt="374bp:"
                            inlineIndex=5
                        if keys[1] == "ASC_Siz10:51-82":
                            keysTxt="70bp:"
                            inlineIndex=0
                        if keys[1] == "ASC_Siz10:310-372":
                            keysTxt="125bp:"
                            inlineIndex=2
                        keysTxt+= "   "
                        
                        if inlineIndex == -1:
                            for tmpIdx in range(len(data["inline"][nameKey]["ratio"])):
                                if inlineData[tmpIdx] == "":
                                    inlineIndex=tmpIdx
                                    break

                        if inlineIndex >= 0:    
                            inlineData[inlineIndex]=keysTxt + str(data["inline"][nameKey]["counts"][keys[0]]) + " / " 
                            inlineData[inlineIndex]+=str(data["inline"][nameKey]["counts"][keys[1]])                            
                            inlineData[inlineIndex]+= " = "+ data["inline"][nameKey]["ratio"][key][:4] + "\n"
                        
                    for inlineIndex in range(len(data["inline"][nameKey]["ratio"])):
                        group["icvals"]+=inlineData[inlineIndex]            
            except:
                pass
            
            
            histograms_first_pass.append(
                {
                    "group": group,
                    "histogram_data": json.dumps(
                        get_histogram_data(archive_path, group["name"])
                    ),
                    "inline_path": inline_path,
                }
            )

        # fill missing sample name based on barcode name match
        # will go by the last matched barcode
        for hist in histograms_first_pass:
            if hist["group"]["sample_name"] == "N/A":
                for barcode_name, sample_name in sample_mapping.items():
                    if barcode_name in hist["group"]["name"]:
                        hist["group"]["sample_name"] = sample_name

        # first sort by sample name, then by index
        # combined barcode has index of -1, so it would go first
        histograms_sorted = sorted(
            histograms_first_pass,
            key=lambda hist: (hist["group"]["sample_name"], hist["group"]["index"]),
        )

        # transform to list of list
        # for hist in histograms_sorted:
        #     histograms.append([
        #         hist["group"],
        #         None,
        #         hist["histogram_data"],
        #         hist["inline_path"]
        #     ])
        histograms = [
            [hist["group"], None, hist["histogram_data"], hist["inline_path"]]
            for hist in histograms_sorted
        ]        
            
    else:
        prefixes = get_read_group_file_prefixes(datasets_object)

        for group in groups:
            prefix = prefixes[group["group"]]
            src_image_path = os.path.join(
                archive_path, "basecaller_results/{}.sparkline.png".format(prefix)
            )
            dst_image_path = os.path.join(
                output_path, "{}.sparkline.png".format(prefix)
            )
            if os.path.exists(src_image_path):
                # Copy to test dir
                shutil.copyfile(src_image_path, dst_image_path)
                histograms.append([group, os.path.basename(dst_image_path), None, None])
            else:
                histograms.append([group, None, None, None])
        # Only Genexus instrument type has this file to link.
        inline_control_stats = False

    write_results_from_template(
        {
            "histograms": histograms,
            "total_reads": total_reads,
            "mean": mean,
            "std": std,
            "cv": (std / mean) * 100.0 if mean != 0.0 else 0,
            "min_percent": (min_read_cound / mean) * 100.0 if mean != 0.0 else 0,
            "inline_control_stats": inline_control_stats,
        },
        output_path,
        os.path.dirname(os.path.realpath(__file__)),
    )
    return print_info("See results for details.")


if __name__ == "__main__":
    execute(archive_path=sys.argv[1], output_path=sys.argv[2], archive_type=sys.argv[3])
