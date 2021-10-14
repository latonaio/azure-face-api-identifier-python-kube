include .env

docker-build:
	bash docker-build.sh

docker-push:
	bash docker-build.sh push

get-env:
	echo "PERSON_GROUP_ID: "$(PERSON_GROUP_ID)
	echo "API_ACCESS_KEY: "$(API_ACCESS_KEY)
	echo "API_ENDPOINT: "$(API_ENDPOINT)

# jqコマンドが必要 brew install jq
get-persons:
	curl -X GET "$(API_ENDPOINT)/face/v1.0/persongroups/$(PERSON_GROUP_ID)/persons" -H "Ocp-Apim-Subscription-Key: $(API_ACCESS_KEY)" | jq

get-person-group:
	curl -X GET "$(API_ENDPOINT)/face/v1.0/persongroups" -H "Ocp-Apim-Subscription-Key: $(API_ACCESS_KEY)" | jq
