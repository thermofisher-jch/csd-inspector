#!/bin/bash

ARCHIVE=$1
OUTPUT=$2

WHOLE_BLOCK_LIST=$ARCHIVE/whole_block_list.txt
if [ -s $WHOLE_BLOCK_LIST ]; then
    filename=$WHOLE_BLOCK_LIST
    HTML=${OUTPUT}/results.html
    echo "<html><head><center><h1>NucStep Trace Plots</h1><head><body>" > ${HTML}

    while read -r line || [[ -n $line ]]; do
        BLOCK=$line
        OUTPUT2=$OUTPUT/$BLOCK
        echo "<br><a href='./${BLOCK}/results.html'> ${BLOCK} </a>" >> ${HTML}
        var=$(./rawTrace_lemon.pl -a $ARCHIVE -o $OUTPUT2 -b $BLOCK 2>&1)

        if [ "$?" != "0" ]; then
          echo N/A
          echo 0
          echo $var
        fi

    done < $filename
    echo "</body></html>" >> ${HTML}

    echo Info
    echo 20
    echo See results for details.

else
    var=$(./rawTrace_lemon.pl -a $ARCHIVE -o $OUTPUT 2>&1)

    if [ "$?" = "0" ]; then
      echo Info
      echo 20
      echo See results for details.
    else
      echo N/A
      echo 0
      echo $var
    fi
fi
