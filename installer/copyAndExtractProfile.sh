#!/usr/bin/env bash
set -e


function main() {
    filePath=$1
    fileName=$2
    
    mkdir -p ./Temp
    cp $filePath/$fileName ./Temp/$fileName
    unzip ./Temp/$fileName -d ./Temp/profiletemp

}


if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi