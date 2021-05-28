#!/bin/bash

cd /var/lib/inspector/media/archive_files
for ii in `ls -d *`
do
	if [ -f $ii/CSA/outputs/SigProcActor-00/Bead_density_1000.png ]
	then
		mkdir -p $ii/test_results/GenexusInstrumentTracker
		unlink $ii/test_results/GenexusInstrumentTracker/Bead_density_1000.png 
		ln -s ../../CSA/outputs/SigProcActor-00/Bead_density_1000.png $ii/test_results/GenexusInstrumentTracker/Bead_density_1000.png
	fi
done
cd -
