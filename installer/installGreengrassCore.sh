#!/usr/bin/env bash
set -e

function createTempDir() {
    temp_install_dir="$(mktemp -d 2>/dev/null)"
    trap "rm -rf -- "$temp_install_dir"" EXIT
    cd $temp_install_dir
}

function setLocalConfig() {
        aws_access_key="$(aws configure get $profileName.aws_access_key_id)"
        aws_secret_access_key="$(aws configure get $profileName.aws_secret_access_key)"
}


function installCore() {
    echo "(INFO) Beginning greengrass core install"
    createTempDir
    export AWS_ACCESS_KEY_ID=$aws_access_key
    export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key
    curl https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip && unzip greengrass-nucleus-latest.zip -d GreengrassCore
    sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE -jar ./GreengrassCore/lib/Greengrass.jar --aws-region $region --thing-name $aws_thing_name --thing-policy-name $aws_thing_policy --tes-role-name $aws_thing_role --tes-role-alias-name $aws_role_alias  --provision true --setup-system-service true --deploy-dev-tools true
}

function main() {
    unset aws_access_key
    unset aws_secret_access_key
    unset aws_thing_name
    unset aws_thing_role
    unset aws_role_alias

    profileName=$1
    region=$2
    aws_thing_name=$3
    aws_thing_role=$4
    aws_thing_policy=$5
    aws_role_alias=$6
    
    setLocalConfig 
    installCore
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi
