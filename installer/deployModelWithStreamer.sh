#!/usr/bin/env bash
set -e

createDeployment() {
    mkdir -p deployments
    cp ./templateFiles/streamer-and-model-deployment.json ./deployments/streamer-and-model-deployment.json
    target="\"VERSION\""
    replace="\"$cliVersion\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-deployment.json

    target="\"streamer\""
    replace="\"$streamerComponent\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-deployment.json

    target="\"model\": "
    replace="\"$modelName\": "
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-deployment.json

    target="\"modelcomponentVersion\": \"1.0.0\""
    replace="\"componentVersion\": \"$modelVersion\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-deployment.json

    target="\"targetArn\": \"\""
    replace="\"targetArn\":  \"arn:aws:iot:$region:$userId:thing/$thingName\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-deployment.json

    target="\"deploymentName\": \"Deployment for \""
    replace="\"deploymentName\": \"Deployment for $thingName\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-deployment.json
}

function updatePolicyFile() {
    mkdir -p ./policies
    cp ./templateFiles/component-artifact-policy-2.json ./policies/component-artifact-policy-2.json
    target="\"Resource\": \"\""
    replace="\"Resource\": \"arn:aws:s3:::$modelBucket\""
    sed -i "s,$target,$replace,g" ./policies/component-artifact-policy-2.json
}

function createPolicy() {
    aws --profile $profileName --region $region iam create-policy --policy-name $thingName-Artifact-Policy-2 --policy-document file://policies/component-artifact-policy-2.json
}

function attachPolicyToCore() {
    aws --profile $profileName --region $region iam attach-role-policy   --role-name $thingName-ExchangeRole  --policy-arn arn:aws:iam::$userId:policy/$thingName-Artifact-Policy-2
}

addAccessToBucket() {
    updatePolicyFile
    createPolicy
    attachPolicyToCore
    echo "(INFO) Sleeping for 20 seconds to allow time for policy to populate in AWS."
    sleep 20s
}

deploy() {
    aws --profile $profileName --region $region greengrassv2 create-deployment --cli-input-json file://deployments/streamer-and-model-deployment.json
}

function main() {
    profileName=$1
    region=$2
    modelName=$3
    modelVersion=$4
    streamerComponent=$5
    userId=$6
    thingName=$7
    modelBucket=$8
    cliVersion=$9
    
    createDeployment
    if [ "$modelBucket" != "" ]; then
        addAccessToBucket
    fi
    deploy

    rm -r policies/ 
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi