#!/usr/bin/env bash
set -e

function main() {
    systemctl stop greengrass.service
    systemctl disable greengrass.service
    rm /etc/systemd/system/greengrass.service
    rm -rf /greengrass/v2
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    main "$@"
fi