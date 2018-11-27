import os


def get_ot_tags(archive_path):
    tags = []

    with open(os.path.join(archive_path, "onetouch.log")) as log:
        script_line = log.readline()
    script = os.path.basename(script_line.split(',')[0])
    script_tag = script.replace(".txt", "")
    script_tag = script_tag.replace("_", " ")
    script_tag = "OT " + script_tag

    tags.append(script_tag)

    return tags
