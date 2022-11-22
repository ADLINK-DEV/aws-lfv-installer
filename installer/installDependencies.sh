#!/usr/bin/env bash
set -e

function createTempDir() {
    temp_install_dir="$(mktemp -d 2>/dev/null)"
    trap 'rm -rf -- "$temp_install_dir"' EXIT
    cd $temp_install_dir
}

function installAWS() {

    if [ "$detectedArch" == "x86_64" ]; then 
        echo "(INFO) installing aws for x86"
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    elif [ "$detectedArch" == "aarch64" ]; then
        echo "(INFO) installing aws for arm"
        curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
    else
        echo "(ERROR) failed to determine machine architecture"
        exit 1
    fi

    unzip awscliv2.zip
    sudo ./aws/install
}

function installCudaAndTensor() {
    echo "(INFO) installing cuda and tensorrt:"
    apt-get install cuda-nvrtc-10-2 \
    tensorrt
}

function installBaseSoftware() {
    apt-get update -y
    apt-get install -y curl \
    default-jdk \
    docker \
    docker-compose \
    unzip \
    python3-pip \
    python3.8-venv 
}

function configureUserGroups() {
    echo "(INFO) configuring usergroups for greengrass:"
    if id ggc_user &> /dev/null; then
    echo "ggc_user exists"
    else
    useradd --system --create-home ggc_user
    fi

    if getent group ggc_group &> /dev/null; then
    echo "ggc_group exists"
    else
    groupadd --system ggc_group
    fi
    usermod -aG docker $USER
    usermod -aG docker ggc_user
    usermod -aG video ggc_user

}

function main() {
    echo -e "\n (INFO) installing required software:"
    installBaseSoftware
    createTempDir

    detectedArch=$1
    awsInstalled=$2

    if [ "$awsInstalled" == "False" ]; then
        installAWS 
    elif [ "$awsInstalled" == "True" ]; then
        echo "(INFO) aws install not required."
    fi

    if [ "$detectedArch" == "aarch64" ]; then
        installCudaAndTensor
    fi

    configureUserGroups
    
}


if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi
