#!/usr/bin/env bash
set -e


function updateDeployment() {
    mkdir -p deployments
    cp ./templateFiles/$fileName  ./deployments/$fileName 
    target="\"targetArn\": \"\""
    replace="\"targetArn\":  \"arn:aws:iot:$region:$userId:thing/$aws_thing_name\""
    sed -i "s,$target,$replace,g" ./deployments/$fileName 

    target="\"deploymentName\": \"Deployment for \""
    replace="\"deploymentName\": \"Deployment for $aws_thing_name\""
    sed -i "s,$target,$replace,g" ./deployments/$fileName

}

function updateBlank() {
    mkdir -p templateFiles/deployments
    cp ./templateFiles/blank-deployment.json templateFiles/deployments/blank-deployment.json
    target="\"targetArn\": \"\""
    replace="\"targetArn\":  \"arn:aws:iot:$region:$userId:thing/$aws_thing_name\""
    sed -i "s,$target,$replace,g" templateFiles/deployments/blank-deployment.json 

    target="\"deploymentName\": \"Deployment for \""
    replace="\"deploymentName\": \"Deployment for $aws_thing_name\""
    sed -i "s,$target,$replace,g" templateFiles/deployments/blank-deployment.json
}

function saveCurrentDeployment() {
    mkdir -p templateFiles/deployments
    cp -f deployments/$fileName templateFiles/deployments/$stage-deployment.json 
}

function removeTempDeployments() {
    rm -r deployments/ 
}

function main() {
    unset aws_thing_name

    region=$1
    fileName=$2
    stage=$3
    aws_thing_name=$4
    userId=$5
    cliVersion=$6
    

    if [ "$#" -gt  "3" ]; then
        updateDeployment
        updateBlank
    fi
    saveCurrentDeployment
    removeTempDeployments
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi
