#!/bin/sh

PERSON_ID="00000000-0000-0000-0000-000000000000"

ENDPOINT="https://"
SUBSCRIPTION_KEY="xxx"
IMAGE_PATH="sample/test_01.jpg"
PERSON_GROUP_ID="parrot"

curl -X POST "${ENDPOINT}/face/v1.0/persongroups/${PERSON_GROUP_ID}/persons/${PERSON_ID}/persistedFaces?detectionModel=detection_01" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}" -H "Content-Type: application/octet-stream" --data-binary "@${IMAGE_PATH}" 
curl "${ENDPOINT}/face/v1.0/persongroups/${PERSON_GROUP_ID}/persons" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}"
curl -X POST "${ENDPOINT}/face/v1.0/persongroups/${PERSON_GROUP_ID}/train" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}" -H "Content-Length: 0"
sleep 3
curl -X GET "${ENDPOINT}/face/v1.0/persongroups/${PERSON_GROUP_ID}/training" -H "Ocp-Apim-Subscription-Key: ${SUBSCRIPTION_KEY}" -H "Content-Length: 0"
