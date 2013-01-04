#!/bin/bash

ARCHIVE=$1
OUTPUT=$2

echo "<html><body>
<h1>A large, clear title explains something important.</h1>
<p>Below that, there are a lot of details.</p>
<ul>
<li>$ARCHIVE</li>
<li>$OUTPUT</li>
</ul>
</body></html>" > $OUTPUT/results.html

echo Warning
echo 30
echo This test always results in a warning.
