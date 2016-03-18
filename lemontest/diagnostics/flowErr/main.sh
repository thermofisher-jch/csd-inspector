#!/bin/bash

ARCHIVE=$1
OUTPUT=$2
ERROR_SUMMARY=${ARCHIVE}/rawlib.ionstats_error_summary.h5

if [ ! -s ${ERROR_SUMMARY} ]; then
    error_summaries=$(ls ${ARCHIVE}/*_rawlib.ionstats_error_summary.h5 | xargs -n1 basename)

    HTML=${OUTPUT}/results.html
    echo "<html><head><center><h1>flowErr Plots</h1><head><body>" > ${HTML}

    for h5file in ${error_summaries}
    do
        BARCODE=${h5file:0:(${#h5file}-33)}
        ERROR_SUMMARY2=${ARCHIVE}/${h5file}
        OUTPUT2=${OUTPUT}/${BARCODE}

        echo "<br><a href='./${BARCODE}/results.html'> ${BARCODE} </a>" >> ${HTML}
        var=$(./flowErr_lemon.pl -e ${ERROR_SUMMARY2} -o $OUTPUT2 2>&1)

        if [ "$?" != "0" ]; then
          echo N/A
          echo 0
          echo $var
        fi

    done
    echo "</body></html>" >> ${HTML}

    echo Info
    echo 20
    echo Plots of flowErr.

else
    var=$(./flowErr_lemon.pl -e ${ERROR_SUMMARY} -o $OUTPUT 2>&1)

    if [ "$?" = "0" ]; then
      echo Info
      echo 20
      echo Plots of flowErr.
    else
      echo N/A
      echo 0
      echo $var
    fi
fi
