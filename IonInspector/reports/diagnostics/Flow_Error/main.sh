#!/bin/bash

ARCHIVE=$1
OUTPUT=$2
ERROR_SUMMARY=${ARCHIVE}/rawlib.ionstats_error_summary.h5

# handle barcode situation
if [ ! -s ${ERROR_SUMMARY} ]; then
    error_summaries=$(ls ${ARCHIVE}/*_rawlib.ionstats_error_summary.h5 2>/dev/null | xargs -n1 basename 2>/dev/null)

    # check if there is no error summary and exit out with a simple message
    if [ -z "$error_summaries" ]; then
        echo "Info"
        echo "20"
        echo "No flow error files were found so no analysis has been done."
        exit
    fi

    HTML=${OUTPUT}/results.html
    echo "<html><head><center><h1>Flow Error Plots</h1><head><body>" > ${HTML}

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
    echo Plots of Flow Error.

else
    var=$(./flowErr_lemon.pl -e ${ERROR_SUMMARY} -o $OUTPUT 2>&1)

    if [ "$?" = "0" ]; then
      echo Info
      echo 20
      echo Plots of Flow Error.
    else
      echo N/A
      echo 0
      echo $var
    fi
fi
