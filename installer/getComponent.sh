#!/usr/bin/env bash
set -e

function saveComponentRecipeToFile() {
    echo arn:aws:greengrass:$region:$userID:components:$modelName:versions:$modelVersion
    mkdir -p ./Temp
    aws --profile $profileName --region $region greengrassv2 get-component \
    --arn arn:aws:greengrass:$region:$userID:components:$modelName:versions:$modelVersion \
    --recipe-output-format YAML \
    --query recipe \
    --output text | base64 --decode > ./Temp/$modelName-recipe.json
}

function main() {
    profileName=$1
    region=$2
    userID=$3
    modelName=$4
    modelVersion=$5
    
    saveComponentRecipeToFile
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi