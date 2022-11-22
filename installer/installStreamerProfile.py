import os
import json
import subprocess
import jsonhelper
import re
import time


def validate(string):
    if re.match(r"^[a-zA-Z0-9-.]*$", string):
        return True
    else:
        print("(ERROR) Chosen streamer component name / stream ID contains invalid special characters, please use \".\" or \"-\" as seperators if required. ")
        return False


class installStreamerProfile:
    def __init__(self):
        self.savedState = jsonhelper.JSONManager()
        self.thingName = self.savedState.getJsonValue(
            "aws_details", "thingName")
        self.profileName = self.savedState.getJsonValue(
            "aws_details", "profileName")
        self.awsRegion = self.savedState.getJsonValue(
            "aws_details", "region")
        self.userIdNo = self.savedState.getJsonValue("aws_details", "UserId")
        self.thingNameLower = self.thingNameLower = self.thingName.lower()
        self.cliVersion = ""
        self.streamerComponentName = ""
        self.profileBase = ""
        self.streamId = ""
        self.pathToProfile = ""
        self.profileFile = ""
        self.defaultStreamId = ""
        self.cameraID = ""
        self.customStreamer = "False"
        self.stage = "4"

    def createDeployStreamerProfile(self):
        session = subprocess.Popen(["./installStreamerProfile.sh " + self.profileName + " " + self.awsRegion + " " + self.thingName + " " +
                                   self.userIdNo + " " + self.streamerComponentName + " " + self.profileBase + " " + 
                                   self.streamId + " " + self.pathToProfile + " " + self.profileFile + " " + 
                                   self.thingNameLower + " " + self.cliVersion + " " + self.customStreamer + " " +self.cameraID], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True



    def checkValidComponentName(self):
        existingComponentList = subprocess.check_output(
            ["aws","--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "list-components"]).strip().decode("utf-8")
        componentToSearch = "\""+self.streamerComponentName+"\""
        if componentToSearch not in existingComponentList:
            print("(INFO) Component name available")
            return True
        else:
            return False

    def nameStreamerComponent(self):
        print()
        print("---------------------------------------")
        print("Enter the a unique name for the streamer component or leave blank to use the default \"" +
              (self.thingName).lower()+".streamer.component\"")
        print("---------------------------------------")
        usr_input = input("\nStreamer Component Name: ")

        try:
            if validate(usr_input):
                if (usr_input != ""):
                    self.streamerComponentName = usr_input
                else:
                    self.streamerComponentName = self.thingNameLower+".streamer.component"
            else:
                self.nameStreamerComponent()
        except:
            return False
        if not self.checkValidComponentName():
            print("(ERROR) Invalid component name already in use")
            self.nameStreamerComponent()
        return True

    def selectProfile(self):
        print()
        print("---------------------------------------")
        print("Enter the file name for the exported profile from the list below (e.g. aws-lfv-edge-basic-streamer.zip)")
        fileList = subprocess.check_output(
            ["ls", self.pathToProfile]).strip().decode("utf-8")
        if fileList == "":
            print("(ERROR) no files found, please try again.")
            self.locateProfile()
        print(fileList)
        print("---------------------------------------")
        usr_input = input("\nProfile file: ")
        fullPath = self.pathToProfile+"/"+usr_input
        try:
            if os.path.isfile(fullPath):

                if usr_input != "":
                    self.profileFile = usr_input
                else:
                    print("(ERROR) no file selected, please try again")
                    self.locateProfile()
            else:
                print("(ERROR) invalid file selected, please try again")
                self.selectProfile()
        except:
            return False

        return True

    def locateProfile(self):
        print()
        print("---------------------------------------")
        print("Enter the full path to the folder containing the downloaded streamer profile (e.g. /home/USERNAME/Downloads)")
        print("---------------------------------------")
        usr_input = input("\nPath to profile: ")

        try:
            if usr_input != "" and os.path.isdir(usr_input):
                self.pathToProfile = usr_input
                if self.selectProfile():
                    return True
                else:
                    return False
            else:
                print("(ERROR) Invalid path provided, please try again.")
                self.locateProfile()
        except:
            return False

    def extractStreamId(self):
        session = subprocess.Popen(["./copyAndExtractProfile.sh " + self.pathToProfile + " " +
                                   self.profileFile], shell=True, env=os.environ.copy())
        session.communicate()

        if self.profileBase == "aws-lfv-edge-basic-streamer":

            with open("./Temp/profiletemp/frame-streamer/adlinkedge/config/FrameStreamer.xml") as xmlFile:
                for line in xmlFile.readlines():
                    if "<StreamId>" in line:
                        fileStreamId = line.strip()
        else:
            with open("./Temp/profiletemp/genicam-streamer/adlinkedge/config/OasysGenICam.xml") as xmlFile:
                for line in xmlFile.readlines():
                    if "<StreamId>" in line:
                        fileStreamId = line.strip()
        fileStreamId = fileStreamId.replace("<StreamId>", "")
        fileStreamId = fileStreamId.replace("</StreamId>", "")
        if fileStreamId != "":
            self.defaultStreamId = fileStreamId
        else:
            self.defaultStreamId = "camera1"
        subprocess.check_output(
            ["rm", "-r", "Temp/"])

    def chooseStreamId(self):
        self.extractStreamId()
        if self.defaultStreamId == "camera1":
            print()
            print("---------------------------------------")
            print("Enter the desired StreamId to be used in the streamer component (Leave blank to use the default \"camera1\")")
            print("---------------------------------------")
        else:
            print()
            print("---------------------------------------")
            print("Enter the desired StreamId to be used in the streamer component (Leave blank to use the detected stream ID \""+self.defaultStreamId+"\")")
            print("---------------------------------------")
        usr_input = input("\nStreamId: ")

        if validate(usr_input):
            if (usr_input == ""):
                self.streamId = self.defaultStreamId
            else:
                self.streamId = usr_input
        else:
            self.chooseStreamId()

    def identifyBase(self):
        print()
        print("---------------------------------------")
        print("Choose the streamer profile base which was used to create the streamer profile:")
        print("1. aws-lfv-edge-basic-streamer")
        print("2. aws-lfv-edge-genicam-streamer")

        print()
        print("Note: The profile should not be renamed on ADLINK Edge Profile Builder.")
        print("---------------------------------------")
        try:
            usr_input = int(input("\nSelect from the options above: "))
            if (usr_input == 1):
                self.profileBase = "aws-lfv-edge-basic-streamer"
            elif (usr_input == 2):
                self.profileBase = "aws-lfv-edge-genicam-streamer"
            else:
                print("Invalid option provided, please try again.")
                self.identifyBase()
        except:
            return False

        return True

    def inform(self):
        print()
        print("---------------------------------------")
        print("Before completing this stage a streamer profile created in ADLINK Edge Profile Builder should be exported to this device. Please complete this action before continuing.")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False
    
    def saveDeployment(self):
        session = subprocess.Popen(["./saveDeployment.sh " + self.awsRegion + " " +
                                    "streamer-profile-deployment.json" + " " + self.stage], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def specifyCamera(self):
        if self.profileBase == "aws-lfv-edge-basic-streamer":
            print()
            print("---------------------------------------")
            print("Please specify the camera identifier to be used by the basic streamer (i.e. \"0\" for /dev/video0)")
            print("Note: Leave blank to use default value \"0\" for /dev/video0.")
            print("---------------------------------------")
        else:
            print()
            print("---------------------------------------")
            print("Please specify the camera ID to be used by the genicam streamer (Typically the device serial number)")
            print("Note: Leave blank to use the first detected camera.")
            print("---------------------------------------")

        try:
            usr_input = input("\nCamera: ")
            if (usr_input == ""):
                if self.profileBase == "aws-lfv-edge-basic-streamer":
                    self.cameraID = "0"
                else:
                    self.cameraID = "ANY"
            else:
                self.cameraID = usr_input
        except:
            return False

        return True

    def chooseProfile(self):
        print()
        print("---------------------------------------")
        print("Choose the streamer profile from the below options:")
        print("1. aws-lfv-edge-basic-streamer template")
        print("2. aws-lfv-edge-genicam-streamer template")
        print("3. Custom streamer profile")
        print()
        print("---------------------------------------")
        try:
            usr_input = int(input("\nSelect from the options above: "))
            if (usr_input == 1):
                self.pathToProfile = "./templateFiles/profiles/"
                self.profileFile = "aws-lfv-edge-basic-streamer.zip"
                self.profileBase = "aws-lfv-edge-basic-streamer"
                if not self.specifyCamera():
                    return False
            elif (usr_input == 2):
                self.pathToProfile = "./templateFiles/profiles/"
                self.profileFile = "aws-lfv-edge-genicam-streamer.zip"
                self.profileBase = "aws-lfv-edge-genicam-streamer"
                if not self.specifyCamera():
                    return False
            elif (usr_input == 3):
                self.customStreamer="True"
                if not self.inform():
                    return False
                if not self.locateProfile():
                    return False
                if not self.identifyBase():
                    return False
            else:
                print("Invalid option provided, please try again.")
                self.chooseProfile()
        except:
            print("Invalid option provided, please try again.")
            return False

        return True

    def getDeployedCliVersion(self):
        time.sleep(5)
        manager = jsonhelper.JSONManager()
        detectCliVersion = self.savedState.getJsonValue("aws_details", "CliVersion")
        if detectCliVersion == "":
            deploymentIDcontainer = subprocess.check_output(
                ["aws","--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "list-effective-deployments", "--core-device-thing-name", self.thingName]).strip().decode("utf-8")
            for line in deploymentIDcontainer.splitlines():
                if "\"deploymentId\"" in line:
                    deploymentId = line.strip()
                    deploymentId = deploymentId.replace("\"deploymentId\": \"", "")
                    deploymentId = deploymentId.replace("\",", "")
                    cliVersionContainer = subprocess.check_output(
                        ["aws","--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "get-deployment", "--deployment-id", deploymentId]).strip().decode("utf-8")
                    for line in cliVersionContainer.splitlines():
                        if "\"componentVersion\"" in line:
                            cliVersion = line.strip()
                            cliVersion = cliVersion.replace("\"componentVersion\": \"", "")
                            cliVersion = cliVersion.replace("\"", "")
            if cliVersion != "":
                self.cliVersion = cliVersion
            else:
                self.cliVersion = "2.8.0"
        else:
            self.cliVersion = detectCliVersion
        manager = jsonhelper.JSONManager()
        manager.updateAWSState("CliVersion", self.cliVersion)

    def run(self):
        if not self.chooseProfile():
            return False
        self.chooseStreamId()
        if not self.nameStreamerComponent():
            return False
        self.getDeployedCliVersion()
        if not self.createDeployStreamerProfile():
            return False
        self.saveDeployment()
        manager = jsonhelper.JSONManager()
        manager.addCreatedResource(
            "S3B","greengrass-component-artifacts-" + self.thingName.lower(), "bucket", 4)
        manager.addCreatedResource(
            "S3P", self.thingName + "-Artifact-Policy-1", "policy", 4)
        manager.addCreatedResource("S3C",self.streamerComponentName, "component", 4)
        manager.updateProfileConfiguration("streamId", self.streamId)
        return True