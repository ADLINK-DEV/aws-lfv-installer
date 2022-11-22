import subprocess
import os
import platform
from shutil import which


class prerequisiteInstaller:
    def __init__(self):
        self.environment = ""
        self.hardware = ""
        self.OS = ""


    def informSudoPermissions(self):
        print()
        print("---------------------------------------")
        print("This stage requires sudo permissions to install software, if you have not recently provided permission you will be prompted for the sudo password.")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def getEnvironment(self):
        self.hardware = platform.machine()
        self.OS = platform.system()
        if self.OS == "Linux" and self.hardware == "x86_64" or self.hardware == "aarch64":
            if self.hardware == "aarch64":
                if self.validateJetpack():
                    return True
                else:
                    print(
                        "(ERROR) The current Jetpack version on the aarch64 machine does not meet requirements")
                    print("Jetpack 4.4/4.5/4.5.1/4.6 is required.")
                    return False
            else:
                if self.checkVersion():
                    return True
                else:
                    print(
                        "(ERROR) A minimum ubuntu version of 18.04 is required for this installer.")
                    return False
        else:
            return False

    def validateJetpack(self):
        print("(INFO) validating jetpack version")
        command = subprocess.check_output(["cat", "/etc/nv_tegra_release"])
        versionString = (command.strip()).decode("utf-8")
        substring = "R32 (release)"
        if substring in versionString:
            return True
        else:
            return False

    def checkVersion(self):
        command = subprocess.check_output(["lsb_release", "-a"])
        versioninfo = (command.strip()).decode("utf-8")
        targetVersions = ["18.04", "20.04", "22.04"]

        for version in targetVersions:
            if version in versioninfo:
                return True
        return False

    def installDependencies(self):
        print("(INFO) Instaling dependencies:")
        aws_install = "False"
        if which("aws"):
            print("(INFO) aws install detected.")
            aws_install = "True"
        session = subprocess.Popen(["sudo ./installDependencies.sh " + self.hardware + " " + aws_install], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def validatePermissionAndRequirements(self):
        if self.environment == False:
            print("(ERROR) Invalid architecture or operating system detected, OS: " +
                  self.OS + ", architecture: " + self.hardware)
            print(
                "This installer supports Linux OS based on ARM (aarch64) or AMD (x86_64) architectures.")
            return False
        else:
            return True

    def run(self):
        if not self.informSudoPermissions():
            return False
        self.environment = self.getEnvironment()
        print("(INFO) Validating system requirements.")
        if not self.validatePermissionAndRequirements():
            return False
        print("(INFO) Beginning dependency installs")
        if not self.installDependencies():
            return False
        return True
