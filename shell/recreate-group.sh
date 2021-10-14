#!/bin/sh

ENDPOINT="https://"
SUBSCRIPTION_KEY="xxx"
PERSON_GROUP_ID="parrot"

curl -v -X DELETE "${ENDPOINT}face/v1.0/persongroups/${PERSON_GROUP_ID}" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}"
curl -v -X PUT "${ENDPOINT}/face/v1.0/persongroups/${PERSON_GROUP_ID}" -H "Content-Type: application/json" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}" -d '{"name":"omotebako"}'
curl -X POST "${ENDPOINT}/face/v1.0/persongroups/${PERSON_GROUP_ID}/persons" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}" -H "Content-Type: application/json" -d "{\"name\":\"Sample\", \"userData\":\"Sample Person\"}"