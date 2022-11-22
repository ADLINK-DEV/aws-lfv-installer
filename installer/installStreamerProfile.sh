#!/usr/bin/env bash
set -e

function createBucket() {
    aws --profile $profileName --region $region s3 mb s3://greengrass-component-artifacts-$thingLower
}

function updatePolicyFile() {
    mkdir -p ./policies
    cp -f ./templateFiles/component-artifact-policy-1.json ./policies/component-artifact-policy-1.json
    target="\"Resource\": \"\""
    replace="\"Resource\": \"arn:aws:s3:::greengrass-component-artifacts-$thingLower/*\""
    sed -i "s,$target,$replace,g" ./policies/component-artifact-policy-1.json
}

function createPolicy() {
    aws --profile $profileName --region $region iam create-policy --policy-name $thingName-Artifact-Policy-1 --policy-document file://policies/component-artifact-policy-1.json
}

function attachPolicyToCore() {
    aws --profile $profileName --region $region iam attach-role-policy   --role-name $thingName-ExchangeRole  --policy-arn arn:aws:iam::$userID:policy/$thingName-Artifact-Policy-1
}

function uploadZip() {
    aws --profile $profileName --region $region s3 cp \
    tempArtifacts/$profileFile \
    s3://greengrass-component-artifacts-$thingLower/$profileFile
}

function createRecipe() {
    mkdir -p recipes
    cp ./templateFiles/streamer-recipe.json ./recipes/streamer-recipe.json
    target="\"URI\": \"\""
    replace="\"URI\": \"s3://greengrass-component-artifacts-$thingLower/$profileFile\""
    sed -i "s,$target,$replace,g" ./recipes/streamer-recipe.json

    target="\"ComponentName\": \"\""
    replace="\"ComponentName\": \"$streamerComponent\""
    sed -i "s,$target,$replace,g" ./recipes/streamer-recipe.json

    target="{artifacts:decompressedPath}/streamer/"
    replace="{artifacts:decompressedPath}/$targetZip/"
    sed -i "s,$target,$replace,g" ./recipes/streamer-recipe.json

}

function copyZip() {
    mkdir -p tempArtifacts
    cp $profilePath/$profileFile tempArtifacts/$profileFile
}

function updateStreamId() {
    cd tempArtifacts/
    unzip $profileFile -d $targetZip

    if [ "$customStreamer" == "False" ]; then
        if [ "$targetZip" == "aws-lfv-edge-basic-streamer" ]; then
            if [ "$cameraId" != "0" ]; then
                target="<Identifier>0</Identifier>"
                replace="<Identifier>$cameraId</Identifier>"

                sed -i "s,$target,$replace,g" ./$targetZip/frame-streamer/adlinkedge/config/FrameStreamer.xml
            fi

        elif [ "$targetZip" == "aws-lfv-edge-genicam-streamer" ]; then
            if [ "$cameraId" != "ANY" ]; then
                target="</StreamConfig>"
                replace="</StreamConfig><GenICamConfig><CameraId>$cameraId</CameraId></GenICamConfig>"

                sed -i "s,$target,$replace,g" ./$targetZip/genicam-streamer/adlinkedge/config/OasysGenICam.xml
            fi
        fi
    fi
    
    target="<StreamId>.*</StreamId>"
    replace="<StreamId>$streamID</StreamId>"

    if [ "$targetZip" == "aws-lfv-edge-basic-streamer" ]; then
        sed -i "s,$target,$replace,g" ./$targetZip/frame-streamer/adlinkedge/config/FrameStreamer.xml
    elif [ "$targetZip" == "aws-lfv-edge-genicam-streamer" ]; then
        sed -i "s,$target,$replace,g" ./$targetZip/genicam-streamer/adlinkedge/config/OasysGenICam.xml
    fi

    rm -r $profileFile
    cd $targetZip
    zip -r $profileFile ./*
    cd ..
    mv $targetZip/$profileFile .
    rm -r $targetZip
    cd ..

}

function createComponent() {
    aws --profile $profileName --region $region greengrassv2 create-component-version --inline-recipe fileb://recipes/streamer-recipe.json
}

createDeployment() {
    mkdir -p deployments
    cp ./templateFiles/streamer-profile-deployment.json ./deployments/streamer-profile-deployment.json
    target="\"VERSION\""
    replace="\"$cliVersion\""
    sed -i "s,$target,$replace,g" ./templateFiles/deployments/3-deployment.json

    target="\"VERSION\""
    replace="\"$cliVersion\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-profile-deployment.json

    target="\"streamer\""
    replace="\"$streamerComponent\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-profile-deployment.json

    target="\"targetArn\": \"\""
    replace="\"targetArn\":  \"arn:aws:iot:$region:$userID:thing/$thingName\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-profile-deployment.json

    target="\"deploymentName\": \"Deployment for \""
    replace="\"deploymentName\": \"Deployment for $thingName\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-profile-deployment.json
}

deploy() {
    aws --profile $profileName --region $region greengrassv2 create-deployment --cli-input-json file://deployments/streamer-profile-deployment.json
}

cleanupFolders() {
    rm -r policies/ recipes/ 
}

function main() {
    profileName=$1
    region=$2
    thingName=$3
    userID=$4
    streamerComponent=$5
    targetZip=$6
    streamID=$7
    profilePath=$8
    profileFile=$9
    thingLower=${10}
    cliVersion=${11}
    customStreamer=${12}
    cameraId=${13}
    
    createBucket
    copyZip
    updatePolicyFile
    updateStreamId
    createPolicy
    attachPolicyToCore
    uploadZip
    echo "(INFO) Sleeping for 20 seconds to allow time for zip to propegate through S3 Bucket."
    sleep 20s
    createRecipe
    createComponent
    createDeployment
    deploy
    cleanupFolders

    rm -r tempArtifacts/
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi
