#!/usr/bin/env bash
set -e

function copyandUnzip() {
    mkdir -p tempArtifacts
    cp $profilePath/$profileFile tempArtifacts/$profileFile
    cd tempArtifacts/
    unzip $profileFile -d $profileBase
}

function updateModel() {
    target="<Name>.*</Name>"
    replace="<Name>$modelName</Name>"

    sed -i "s,$target,$replace,g" ./$profileBase/aws-lookout-vision/adlinkedge/config/AWSLookoutVision.xml
}

function updateBucket() {

    target="<Bucket>.*</Bucket>"
    replace="<Bucket>$inferenceBucket</Bucket>"
    sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml

    if [ -z "$inferenceBucketFolder" ] && [ "$folderDetected" == "True" ]; then

        target="<Folder>.*</Folder>"
        replace=""
        sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml
    elif [ "$folderDetected" == "True" ]; then

        target="<Folder>.*</Folder>"
        replace="<Folder>/$inferenceBucketFolder</Folder>"
        sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml
    elif [ -n "$inferenceBucketFolder" ] && [ "$folderDetected" == "False" ]; then

        target="</CreateBucket>"
        replace="</CreateBucket><Folder>/$inferenceBucketFolder</Folder>"
        sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml
    fi
}

function updateStreamID() {

    target="<SourceStreamId>.*</SourceStreamId>"
    replace="<SourceStreamId>$targetStreamId</SourceStreamId>"

    sed -i "s,$target,$replace,g" ./$profileBase/aws-lookout-vision/adlinkedge/config/AWSLookoutVision.xml

    target="<StreamId>.*</StreamId>"
    replace="<StreamId>$targetStreamId</StreamId>"

    sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml

}

function updateGreengrassOptionalFilter() {

    target="<FlowID>.*</FlowID>"
    replace="<FlowID>$targetStreamId.$inferenceEngine</FlowID>"

    sed -i "s,$target,$replace,g" ./$profileBase/greengrass-connect/adlinkedge/config/GreengrassConnect.xml
}

function updateNodeRed() {

    target="\"filtersFlowId\":\"camera1.lfv\""
    replace="\"filtersFlowId\":\"$targetStreamId.$inferenceEngine\""

    sed -i "s,$target,$replace,g" ./$profileBase/node-red/adlinkedge/config/flows.json

    target="\"filtersFlowId\":\"camera1\""
    replace="\"filtersFlowId\":\"$targetStreamId\""

    sed -i "s,$target,$replace,g" ./$profileBase/node-red/adlinkedge/config/flows.json

}

function updateRegion() {

    target="<Region>.*</Region>"
    replace="<Region>$region</Region>"
    sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml
}

function updateTopic() {

    target="<Topic>.*</Topic>"
    replace="<Topic>$topic</Topic>"

    sed -i "s,$target,$replace,g" ./$profileBase/greengrass-connect/adlinkedge/config/GreengrassConnect.xml
}

function fixBlankTemplate() {

    target="<Region/>"
    replace="<Region>$region</Region>"
    sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml

    target="<Bucket/>"
    replace="<Bucket>$inferenceBucket</Bucket>"
    sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml

    if [ -z $inferenceBucketFolder ];then
        target="<Folder/>"
        replace=""
        sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml
    else
        target="<Folder/>"
        replace="<Folder>/$inferenceBucketFolder</Folder>"
        sed -i "s,$target,$replace,g" ./$profileBase/training-streamer/adlinkedge/config/TrainingStreamer.xml
    fi

    target="<Name/>"
    replace="<Name>$modelName</Name>"

    sed -i "s,$target,$replace,g" ./$profileBase/aws-lookout-vision/adlinkedge/config/AWSLookoutVision.xml
}

function rezip() {
    rm -r $profileFile
    cd $profileBase
    zip -r $profileBase.zip ./*
    cd ..
    mv $profileBase/$profileBase.zip .
    rm -r $profileBase
    cd ..
}

function configureProfile() {
    copyandUnzip
    updateBucket
    updateModel
    updateRegion
    updateStreamID
    updateNodeRed
    updateTopic
    updateGreengrassOptionalFilter
    if [ $blankTemplate == "True" ]; then
        fixBlankTemplate
    fi
    rezip
}

function uploadZip() {
    aws --profile $profileName --region $region s3 cp \
    tempArtifacts/$profileBase.zip \
    s3://greengrass-component-artifacts-$thingLower/$profileBase.zip
}

function removeTempArtifacts() {
    rm -r tempArtifacts/
}

function createPolicy() {
    mkdir -p ./policies
    cp -f ./templateFiles/component-artifact-policy-3.json ./policies/component-artifact-policy-3.json
    aws --profile $profileName --region $region iam create-policy --policy-name $thingName-Artifact-Policy-3 --policy-document file://policies/component-artifact-policy-3.json
}

function attachPolicyToCore() {
    aws --profile $profileName --region $region iam attach-role-policy   --role-name $thingName-ExchangeRole  --policy-arn arn:aws:iam::$userId:policy/$thingName-Artifact-Policy-3
}

function createBucket() {
    if [ "$bucketExists" == "False" ]; then
        aws --profile $profileName s3api create-bucket --bucket "$inferenceBucket" --region "$region" --create-bucket-configuration LocationConstraint\="$region"
    fi
}

function createRecipe() {
    mkdir -p recipes
    cp ./templateFiles/inference-recipe.json ./recipes/inference-recipe.json
    target="\"URI\": \"\""
    replace="\"URI\": \"s3://greengrass-component-artifacts-$thingLower/$profileBase.zip\""
    sed -i "s,$target,$replace,g" ./recipes/inference-recipe.json

    target="\"ComponentName\": \"\""
    replace="\"ComponentName\": \"$inferenceComponentName\""
    sed -i "s,$target,$replace,g" ./recipes/inference-recipe.json

    target="{artifacts:decompressedPath}/inference/"
    replace="{artifacts:decompressedPath}/$profileBase/"
    sed -i "s,$target,$replace,g" ./recipes/inference-recipe.json

}

function createComponent() {
    aws --profile $profileName --region $region greengrassv2 create-component-version --inline-recipe fileb://recipes/inference-recipe.json
}

function createDeployment() {
    mkdir -p deployments
    cp ./templateFiles/streamer-and-model-and-inference-deployment.json ./deployments/streamer-and-model-and-inference-deployment.json
    target="\"VERSION\""
    replace="\"$cliVersion\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json

    target="\"streamer\""
    replace="\"$streamerComponent\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json

    target="\"model\": "
    replace="\"$modelName\": "
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json

    target="\"inference\": "
    replace="\"$inferenceComponentName\": "
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json

    target="\"modelcomponentVersion\": \"1.0.0\""
    replace="\"componentVersion\": \"$modelVersion\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json

    target="\"targetArn\": \"\""
    replace="\"targetArn\":  \"arn:aws:iot:$region:$userId:thing/$thingName\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json

    target="\"deploymentName\": \"Deployment for \""
    replace="\"deploymentName\": \"Deployment for $thingName\""
    sed -i "s,$target,$replace,g" ./deployments/streamer-and-model-and-inference-deployment.json
}

function deploy() {
    aws --profile $profileName --region $region greengrassv2 create-deployment --cli-input-json file://deployments/streamer-and-model-and-inference-deployment.json
}

function cleanup() {
    rm -r  recipes/ policies/
}

function main() {
    profileName=$1
    region=$2
    thingName=$3
    thingLower=$4
    inferenceComponentName=$5
    userId=$6
    profileBase=$7
    profilePath=$8
    profileFile=$9
    cliVersion=${10}
    topic=${11}
    inferenceBucket=${12}
    inferenceEngine=${13}
    targetStreamId=${14}
    folderDetected=${15}
    bucketExists=${16}
    streamerComponent=${17}
    modelName=${18}
    modelVersion=${19}
    blankTemplate=${20}
    inferenceBucketFolder=${21}

    configureProfile
    uploadZip
    echo "(INFO) Sleeping for 20 seconds to allow time for zip to propegate through S3 Bucket."
    sleep 20s
    removeTempArtifacts 
    createBucket
    createPolicy
    attachPolicyToCore
    createRecipe 
    createComponent 
    createDeployment 
    deploy
    cleanup
}


if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi