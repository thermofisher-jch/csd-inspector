#!/bin/bash


# curl 'http://vulcan.itw:3333/project?project=2273124461984' \
csrf_token=`curl 'http://vulcan.itw:3333/command/core/get-csrf-token' \
  -H 'Connection: keep-alive' \
  -H 'Pragma: no-cache' \
  -H 'Cache-Control: no-cache' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: OpenRefine Automation Script' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Referer: http://vulcan.itw:3333/' \
  -c ./cookie_jar.dat \
  --compressed \
  --insecure | jq -r '.token'`

job_id=`curl 'http://vulcan.itw:3333/command/core/create-importing-job' \
  -H 'Connection: keep-alive' \
  -H 'Pragma: no-cache' \
  -H 'Cache-Control: no-cache' \
  -H 'User-Agent: OpenRefine Automation Script' \
  -H 'Accept: application/json, text/javascript, */*; q=0.01' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Origin: http://vulcan.itw:3333' \
  -H 'Referer: http://vulcan.itw:3333/' \
  -b './cookie_jar.dat' \
  --data-raw "csrf_token=${csrf_token}" \
  --compressed \
  --insecure | jq -r '.jobID'`

echo "Got <${job_id}>"

# curl "http://vulcan.itw:3333/command/core/importing-controller?controller=core%2Fdefault-importing-controller&jobID=${job_id}&subCommand=load-raw-data&csrf_token=${csrf_token}" \
start_data=`curl "http://vulcan.itw:3333/command/core/create-project-from-upload?csrf_token=${csrf_token}&jobID=${job_id}" \
  -X 'POST' \
  -H 'Connection: keep-alive' \
  -H 'Pragma: no-cache' \
  -H 'Cache-Control: no-cache' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: OpenRefine Automation Script' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Origin: http://vulcan.itw:3333' \
  -H 'Referer: http://vulcan.itw:3333/' \
  -b './cookie_jar.dat' \
  -F 'controller=core/default-importing-controller' \
  -F 'subCommand=load-raw-data' \
  -F "csrf_token=${csrf_token}" \
  -F "jobID=${job_id}" \
  -F 'project-file=@/tmp/export.dat' \
  -F 'project-name=prod_archive_backfill' \
  -F 'format=text/line-based/csv' \
  -F 'options={"encoding":"US-ASCII","separator":"|","ignoreLines":-1,"headerLines":1,"skipDataLines":0,"limit":-1,"storeBlankRows":true,"guessCellValueTypes":false,"processQuotes":false,"storeBlankCellsAsNulls":true,"includeFileSources":false,"trimStrings":false,"columnNames":["id","site","submitter_name","archive_type","doc_file","search_tags"],"projectName":"prod_archive_backfill","projectTags":["production","raw_archives_table","derived_instrument_analysis"],"fileSource":"exported.dat"}]' \
  --compressed \
  --insecure`
job_id=`echo ${start_data} | jq .job.id`
echo "Upload sent!"
echo ${start_data}
echo ${job_id}
echo "Now polling!"

while [ true ]
do
	curl "http://vulcan.itw:3333/command/core/get-importing-job-status?jobID=${job_id}&csrf_token=${csrf_token}" \
	  -X 'POST' \
	  -H 'Connection: keep-alive' \
	  -H 'Content-Length: 0' \
	  -H 'Pragma: no-cache' \
	  -H 'Cache-Control: no-cache' \
	  -H 'Accept: application/json, text/javascript, */*; q=0.01' \
	  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36' \
	  -H 'X-Requested-With: XMLHttpRequest' \
	  -H 'Origin: http://vulcan.itw:3333' \
	  -H 'Referer: http://vulcan.itw:3333/' \
	  -H 'Accept-Language: en-US,en;q=0.9' \
	  --compressed \
	  --insecure ;
	sleep 5
done
