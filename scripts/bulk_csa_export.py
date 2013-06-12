#!/usr/bin/env python

from multiprocessing import Pool, Lock
import requests
import json
import time
import argparse
import urlparse
import traceback
import os
import os.path
from datetime import datetime


root_path = 'tmp'
auth = ('ionadmin', 'ionadmin')
g = {}


def log(message):
    g['lock'].acquire()
    print(message)
    g['lock'].release()


def logged_get_archive(*args, **kwargs):
    try:
        return get_archive(*args, **kwargs)
    except Exception as err:
        log(traceback.format_exc())


def download_result(experiment, url_path):
    result_url = urlparse.urljoin(g['server_url'], url_path)
    result_response = requests.get(result_url, auth=auth)
    if result_response.ok:
        return result_response.json()
    else:
        log("{:<4d} failed downloading {}".format(experiment['id'], result_url))
        with open(os.path.join(directory, "errors.log"), 'w') as errlog:
            errlog.write("HTTP {} {}\n".format(result_response.status_code, result_response.reason))
            errlog.write(result_response.content)
            errlog.write("\n")


def download_csa(experiment, result, directory):
    url_path = "/report/{:d}/CSA.zip".format(result['id'])
    csa_url = urlparse.urljoin(g['server_url'], url_path)
    response = requests.get(csa_url, stream=True, auth=auth)
    if response.ok:
        with open(os.path.join(directory, "csa.zip"), 'wb') as csa:
            for data in response.iter_content(4096):
                csa.write(data)
        log("Experiment {:<4d} downloaded CSA".format(experiment['id']))
    else:
        log("{:<4d} failed up downloading {}".format(experiment['id'], csa_url))
        with open(os.path.join(directory, "errors.log"), 'w') as errlog:
            errlog.write("HTTP {} {}\n".format(response.status_code, response.reason))
            errlog.write(response.content)
            errlog.write("\n")


def get_archive(experiment):
    directory = os.path.join(g['server_path'], str(experiment['id']))
    os.mkdir(directory)
    with open(os.path.join(directory, "experiment.json"), 'w') as output:
        json.dump(experiment, output, sort_keys=True, indent=4)
    for url_path in experiment.get("results", []):
        result = download_result(experiment, url_path)
        if result and result.get("status", None) == "Completed":
            break
    else:
        log("server {} experiment {:d} had no complete results".format(g['hostname'], experiment['id']))
        return
    with open(os.path.join(directory, "result.json"), 'w') as output:
        json.dump(result, output, sort_keys=True, indent=4)
    download_csa(experiment, result, directory)


def init(process_globals):
    g.update(process_globals)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("server_url")
    parser.add_argument("api_file")
    args = parser.parse_args()
    api_data = json.load(open(args.api_file))
    print("Loaded {} Experiment records.".format(api_data['meta']['total_count']))
    experiments = api_data['objects'][:130]
    
    start_time = datetime.now()
    g['server_url'] = args.server_url
    g['hostname'] = urlparse.urlparse(args.server_url).hostname
    g['server_path'] = os.path.join(root_path, g['hostname'])
    if not os.path.exists(g['server_path']):
        os.mkdir(g['server_path'])
    # Process pool handling
    g['lock'] = Lock()
    workers = Pool(4, init, (g,))
    result = workers.map_async(logged_get_archive, experiments, 1)
    workers.close()
    print("Closed: waiting for completion...")
    workers.join()

    end_time = datetime.now()

    print("Finished like a boss in {}.".format(end_time - start_time))

if __name__ == "__main__":
    main()