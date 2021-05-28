#!/bin/bash


project_id="${1}"
if [[ ! ${project_id} ]];
then
	echo "Project ID parameter required!"
	exit 1;
fi

operations_file="${2}"
if [[ -f ${operations_file} ]];
then
	operations="$(cat ${operations_file})"
else
	echo "Using default just_imports.json operations"
	operations="$(cat ./just_imports.json)"
fi

echo "Get CSRF Token"

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

echo "Call apply-operations"

op_status=`curl "http://vulcan.itw:3333/command/core/apply-operations?project=${project_id}" \
  -H 'Pragma: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Cache-Control: no-cache' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: OpenRefine Automation Script' \
  -H 'Accept: application/json, text/javascript, */*; q=0.01;' \
  -H 'Accept-Encoding: gzip, deflate' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Origin: http://vulcan.itw:3333' \
  -H "Referer: http://vulcan.itw:3333/project?project=${project_id}" \
  -b './cookie_jar.dat' \
  --data-urlencode "operations=${operations}" \
  --data "csrf_token=${csrf_token}" \
  --compressed \
  --insecure`

echo "Got <${op_status}>"

