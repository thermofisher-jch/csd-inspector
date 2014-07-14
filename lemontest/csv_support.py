'''
Author: Anthony Rodriguez
File: metrics_pgm.py
Created: 11 July 2014
Last Modified: 11 July 2014
'''

import csv
import StringIO

def make_csv(metrics, headers):
    
    output = StringIO.StringIO()
    
    csv_writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    
    csv_writer.writerow(headers)
    
    for metric in metrics:
        
        row = [
               metric.archive.id,
               metric.archive.label,
               metric.pgm_temperature,
               metric.pgm_pressure,
               metric.chip_temperature,
               metric.chip_noise,
               metric.seq_kit,
               metric.chip_type,
               metric.isp_loading,
               metric.system_snr
               ]

        csv_writer.writerow(row)
        
    return output.getvalue()