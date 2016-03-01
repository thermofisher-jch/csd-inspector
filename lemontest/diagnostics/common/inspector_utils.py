import os

def read_explog(archive_path):
    """
    This method will read and output a array of colon delimited key/value pairs from the explog_final.txt
    :param archive_path: the root directory of the archive
    :return:
    """
    path = os.path.join(archive_path, "explog_final.txt")
    if not os.path.exists(path):
        raise Exception("explog_final.txt missing")

    # parse the log file for all of the values in a colon delimited parameter
    data = {}
    for line in open(path):
        # Trying extra hard to accommodate formatting issues in explog
        datum = line.split(":", 1)
        if len(datum) == 2:
            key, value = datum
            data[key.strip()] = value.strip()

    return data

def print_ok(message):
    """
    prints the ok message to controlling parent
    :param message: The message to print
    """
    print("OK")
    print(10)
    print(message)

def print_na(message):
    """
    prints the na message to the controlling parent
    :param message:
    """
    print("N/A")
    print(0)
    print(message)
