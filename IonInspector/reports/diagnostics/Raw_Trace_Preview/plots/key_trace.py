def parse_key_traces(lines):
    data = []
    for line in lines:
        flow, nuc, xmin, xmax, ymin, ymax, count, vals = line.split("\t", 7)
        if int(flow) < 8:
            data.append(
                [
                    int(flow),
                    nuc,
                    {"xmin": int(xmin), "xmax": int(xmax), "ymin": int(ymin), "ymax": int(ymax), "count": int(count)},
                    [float(i) for i in vals.split()]
                ]
            )
        if len(data) == 8:
            break
    return sorted(data, key=lambda x: x[0])


def get_nuc_flows(target_nuc, key="TCAG", flow_order="TACGTACGTCTGAGCATCGATCGATGTACAGC"):
    first_incorp_flow = None
    first_non_incorp_flow = None
    current_key_nuc = 0
    for flow_number, flow_nuc in enumerate(flow_order):
        # If this flow will incorporate
        if flow_nuc == key[current_key_nuc]:
            if flow_nuc == target_nuc:
                first_incorp_flow = flow_number
            current_key_nuc += 1
            if current_key_nuc >= len(key):
                break
        # If this flow will not
        elif first_non_incorp_flow is None and flow_nuc == target_nuc:
            first_non_incorp_flow = flow_number

    return first_incorp_flow, first_non_incorp_flow


def get_key_traces_dygraphs_data(key_trace_regions, frame_starts):
    dygraphs_key_trace_titles = []
    dygraphs_key_trace_labels = ["Time"] + ["T", "C", "A", "G"]
    dygraphs_key_trace_data = []

    for label, bead_lines, empty_lines in key_trace_regions:
        dygraphs_key_trace_titles.append(label)
        bead_well_data = parse_key_traces(bead_lines)
        empty_well_data = parse_key_traces(empty_lines)

        # Compute background subtracted traces
        data = [[i, None, None, None, None] for i in frame_starts]

        for i, nuc in enumerate("TCAG"):
            first_incrop_flow_index, first_non_incorp_flow_index = get_nuc_flows(nuc)

            bead_well_incorp_flow = bead_well_data[first_incrop_flow_index]
            bead_well_non_incrop_flow = bead_well_data[first_non_incorp_flow_index]

            empty_well_incorp_flow = empty_well_data[first_incrop_flow_index]
            empty_well_non_incrop_flow = empty_well_data[first_non_incorp_flow_index]

            # Based on the flow order we already know what nuc each flow should be in these files. Make sure it matches.
            assert bead_well_incorp_flow[1] == nuc, "%s in file vs %s" % (bead_well_incorp_flow[0], nuc)

            incorp_diff = [a - b for a, b in zip(bead_well_incorp_flow[3], empty_well_incorp_flow[3])]
            non_incorp_diff = [a - b for a, b in zip(bead_well_non_incrop_flow[3], empty_well_non_incrop_flow[3])]

            for j, value in enumerate([round(a - b, 3) for a, b in zip(incorp_diff, non_incorp_diff)]):
                data[j][i + 1] = value

        dygraphs_key_trace_data.append(data)

    # compute max across graphs
    dygraphs_key_trace_max = 0
    for region in dygraphs_key_trace_data:
        for frame in region:
            dygraphs_key_trace_max = max(frame[1:] + [dygraphs_key_trace_max])
    dygraphs_key_trace_max += 5

    return {
        "dygraphs_key_trace_titles": dygraphs_key_trace_titles,
        "dygraphs_key_trace_labels": dygraphs_key_trace_labels,
        "dygraphs_key_trace_data": dygraphs_key_trace_data,
        "dygraphs_key_trace_max": dygraphs_key_trace_max
    }
