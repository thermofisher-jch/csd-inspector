#!/bin/sh

test_dir="${1}"
cd "${test_dir}"

echo "${test_dir}"
/usr/bin/mutool extract ../../report.pdf 8
ls
/bin/mv img-0008.png Bead_density_1000.png

cd -
