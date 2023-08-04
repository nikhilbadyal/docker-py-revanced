#!/bin/bash


client_id="test"
path="apks/options.json"
json_data=$(cat "${path}")

new_object='{
"patchName": "Spoof client",
"options": [
  {
    "key": "client-id",
    "value": "'${client_id}'"
  }
]
}'
# Check if an object with the patchName "Spoof client" already exists
existing_object_index=$(echo "${json_data}" | jq 'map(.patchName) | index("Spoof client")')
echo "${existing_object_index}"
if [[ ${existing_object_index} != "null" ]]; then
  echo "Exist"
  updated_json=$(echo "${json_data}" | jq ".[${existing_object_index}].options[0].value = \"${client_id}\"")
else
  echo "Does not exist"
  updated_json=$(echo "${json_data}" | jq ". += [${new_object}]")
fi
echo "${updated_json}" > "${path}"
