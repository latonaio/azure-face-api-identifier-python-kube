#!/bin/sh
PERSON_GROUP_ID="parrot"
API_ACCESS_KEY="xxx"
API_ENDPOINT="https://"

SCRIPT_DIR=$(cd $(dirname $0); pwd)
TARGET_FILE1="face-api-config.json"
TARGET_FILE2=".env"

cd ${SCRIPT_DIR}
cd ..
cp ${TARGET_FILE1}.sample ${TARGET_FILE1}
cp ${TARGET_FILE2}.sample ${TARGET_FILE2}

sed -e "s/\"PERSON_GROUP_ID\":.*\"/\"PERSON_GROUP_ID\": \"${PERSON_GROUP_ID}\"/g" \
    -e "s/\"API_ACCESS_KEY\":.*\"/\"API_ACCESS_KEY\": \"${API_ACCESS_KEY}\"/g" \
    -e "s!\"API_ENDPOINT\":.*\"!\"API_ENDPOINT\": \"${API_ENDPOINT}\"!g" \
    ${TARGET_FILE1} > temp1.yml
    
sed -e "s/PERSON_GROUP_ID=.*/PERSON_GROUP_ID=\"${PERSON_GROUP_ID}\"/g" \
    -e "s/API_ACCESS_KEY=.*/API_ACCESS_KEY=\"${API_ACCESS_KEY}\"/g" \
    -e "s!API_ENDPOINT=.*!API_ENDPOINT=\"${API_ENDPOINT}\"!g" \
    ${TARGET_FILE2} > temp2.yml

rm ${TARGET_FILE1} ${TARGET_FILE2}
mv temp1.yml ${TARGET_FILE1}
mv temp2.yml ${TARGET_FILE2}

cp ${TARGET_FILE1} ../azure-face-api-registrator-kube/${TARGET_FILE1}
cp ${TARGET_FILE2} ../azure-face-api-registrator-kube/${TARGET_FILE2}