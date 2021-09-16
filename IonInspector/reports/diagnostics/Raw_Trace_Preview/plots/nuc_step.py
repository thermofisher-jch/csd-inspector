NUC_STEP_FILES = [
    ["Inlet", "NucStep_inlet_step.txt"],
    ["Middle", "NucStep_middle_step.txt"],
    ["Outlet", "NucStep_outlet_step.txt"],
]

NUC_ORDER = {"A": 0, "C": 1, "T": 2, "G": 3}


def parse_nuc_step_lines(lines):
    data = []
    for line in lines:
        flow, nuc, val = line.split("\t")
        row = [int(flow), None, None, None, None]
        row[1 + NUC_ORDER[nuc]] = float(val)
        data.append(row)
    return sorted(data, key=lambda x: x[0])


def get_nuc_step_dygraphs_data(archive_path):
    # nuc step
    dygraphs_nuc_step_titles = []
    dygraphs_nuc_step_labels = ["Flow"] + NUC_ORDER.keys()
    dygraphs_nuc_step_data = []

    for label, filename in NUC_STEP_FILES:
        with open(archive_path + "/sigproc_results/NucStep/" + filename) as fp:
            dygraphs_nuc_step_titles.append(label)
            dygraphs_nuc_step_data.append(parse_nuc_step_lines(fp))

    dygraphs_nuc_step_max = 0
    for region in dygraphs_nuc_step_data:
        for row in region:
            dygraphs_nuc_step_max = max(row[1:] + [dygraphs_nuc_step_max])
    dygraphs_nuc_step_max += 50

    return {
        "dygraphs_nuc_step_titles": dygraphs_nuc_step_titles,
        "dygraphs_nuc_step_data": dygraphs_nuc_step_data,
        "dygraphs_nuc_step_labels": dygraphs_nuc_step_labels,
        "dygraphs_nuc_step_max": dygraphs_nuc_step_max,
    }
