import os
import subprocess
import jsonhelper
import re


def validate(string):
    if re.match(r"^[a-z0-9-./]*$", string):
        return True
    else:
        print("(ERROR) Chosen bucket name / topic contains invalid special characters or captials, please use \".\" or \"-\" as seperators if required. ")
        return False


class inferenceProfileDeployer:
    def __init__(self):
        self.savedState = jsonhelper.JSONManager()
        self.thingName = self.savedState.getJsonResourceName(
            "S2C")
        self.artifactBucket = self.savedState.getJsonResourceName(
            "S3B")
        self.cliVersion = self.savedState.getJsonValue(
            "aws_details", "CliVersion")
        self.userId = self.savedState.getJsonValue(
            "aws_details", "UserId")
        self.streamId = self.savedState.getJsonValue(
            "profile_configuration", "streamId")
        self.profileName = self.savedState.getJsonValue(
            "aws_details", "profileName")
        self.awsRegion = self.savedState.getJsonValue(
            "aws_details", "region")
        self.streamerComponentName = self.savedState.getJsonResourceName("S3C")
        self.modelComponentName = self.savedState.getJsonValue("aws_details", "deployedModelName")
        self.modelComponentVersion = self.savedState.getJsonValue("aws_details", "deployedModelVersion")
        self.pathToProfile = ""
        self.profileFile = ""
        self.topic = ""
        self.inferenceBucket = ""
        self.inferenceBucketFolder = ""
        self.inferenceEngine = ""
        self.inferenceComponentName = ""
        self.thingNameLower = ""
        self.modelName = ""
        self.bucketExists = "True"
        self.folderDetected = "False"
        self.blankTemplate = "False"
        self.customInference = "False"
        self.stage = "6"

    def deployInference(self):
        print("(INFO) Deploying inference profile.")
        session = subprocess.Popen(["./deployInferenceModelandStreamer.sh " +self.profileName + " " + self.awsRegion + " " + self.thingName + " " +
                                   self.thingNameLower + " " + self.inferenceComponentName + " " + self.userId + " " +
                                    self.profileBase + " " + self.pathToProfile + " " + self.profileFile + " " +
                                    self.cliVersion + " " + self.topic + " " + self.inferenceBucket + " " +
                                    self.inferenceEngine + " " + self.streamId + " " + self.folderDetected + " " +
                                    self.bucketExists  + " " + self.streamerComponentName + " " + self.modelComponentName + " " +
                                    self.modelComponentVersion + " " + self.blankTemplate + " " + self.inferenceBucketFolder ], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def checkValidComponentName(self):
        existingComponentList = subprocess.check_output(
            ["aws","--profile", self.profileName, "--region", self.awsRegion,  "greengrassv2", "list-components"]).strip().decode("utf-8")
        componentToSearch = "\""+self.inferenceComponentName+"\""
        if componentToSearch not in existingComponentList:
            print("(INFO) Component name available")
            return True
        else:
            return False

    def selectProfile(self):
        print()
        print("---------------------------------------")
        print("Enter the file name for the exported profile from the list below (e.g. aws-lfv-edge-inference.zip)")
        fileList = subprocess.check_output(
            ["ls", self.pathToProfile]).strip().decode("utf-8")
        if fileList == "":
            print("(ERROR) no files found, please try again.")
            self.locateProfile()
        print(fileList)
        print("---------------------------------------")
        usr_input = input("\nProfile file: ")
        fullPath = self.pathToProfile+"/"+usr_input
        if os.path.isfile(fullPath):
            if usr_input != "":
                self.profileFile = usr_input
                self.profileBase = "aws-lfv-edge-inference"
            else:
                print("(ERROR) no file selected, please try again")
                self.locateProfile()
        else:
            print("(ERROR) invalid file selected, please try again")
            self.selectProfile()

    def locateProfile(self):
        print()
        print("---------------------------------------")
        print("Enter the full path to the folder containing the downloaded inference profile (e.g. /home/USERNAME/Downloads)")
        print("---------------------------------------")
        usr_input = input("\nPath to profile: ")

        if usr_input != "" and os.path.isdir(usr_input):
            self.pathToProfile = usr_input
            if self.selectProfile():
                return True
            else:
                return False
        else:
            print("(ERROR) Invalid path provided, please try again.")
            self.locateProfile()

    def copyProfile(self):
        session = subprocess.Popen(["./copyAndExtractProfile.sh " + self.pathToProfile + " " +
                                   self.profileFile], shell=True, env=os.environ.copy())
        session.communicate()

    def updateTopic(self):
        topicSegments = self.topic.split("/")
        topicSegments[len(topicSegments)-1] = self.streamId
        delimiter = "/"
        self.topic = delimiter.join(topicSegments)

    def extractTopic(self):
        topic = ""
        with open("./Temp/profiletemp/greengrass-connect/adlinkedge/config/GreengrassConnect.xml") as xmlFile:
            for line in xmlFile.readlines():
                if "<Topic>" in line:
                    topic = line.replace("<Topic>", "")
                    topic = topic.replace("</Topic>", "")
                    topic = topic.strip()
        if topic != "":
            self.topic = topic
            self.updateTopic()

    def changeTopic(self):
        defaultTopic = "adlink/datariver/" + self.streamId
        if self.topic == "":
            print()
            print("---------------------------------------")
            print("Enter the topic to publish inference results to (Leave blank to use the default topic \""+defaultTopic+"\")")
            print("---------------------------------------")
        else:
            print()
            print("---------------------------------------")
            print("Enter the topic to publish inference results to (Leave blank to use the detected topic and stream ID \""+self.topic+"\")")
            print("---------------------------------------")
            
        usr_input = input("\nTopic: ")
        if validate(usr_input):
            if (usr_input != ""):
                self.topic = usr_input
            elif (self.topic == ""):
                self.topic == defaultTopic
        else:
            self.changeTopic()

    def checkForEmpties(self):
        region = False
        bucket = False
        folder = False
        name = False
        with open("./Temp/profiletemp/training-streamer/adlinkedge/config/TrainingStreamer.xml") as xmlFile:
            for line in xmlFile.readlines():
                if "<Region/>" in line:
                    region=True
                elif "<Bucket/>" in line:
                    bucket=True
                elif "<Folder/>" in line:
                    folder=True
        with open("./Temp/profiletemp/aws-lookout-vision/adlinkedge/config/AWSLookoutVision.xml") as xmlFile:
            for line in xmlFile.readlines():
                if "<Name/>" in line:
                    name=True

        if region or bucket or folder or name:
            self.blankTemplate = "True"


    def extractBucket(self):
        bucket = ""
        folder = ""
        with open("./Temp/profiletemp/training-streamer/adlinkedge/config/TrainingStreamer.xml") as xmlFile:
            for line in xmlFile.readlines():
                if "<Bucket>" in line:
                    bucket = line.strip()
                elif "<Folder>" in line:
                    folder = line.strip()
                    self.folderDetected = "True"
        if bucket != "":
            bucket = bucket.replace("<Bucket>", "")
            bucket = bucket.replace("</Bucket>", "")
            if bucket != "":
                self.inferenceBucket = bucket
            if folder != "":
                folder = folder.replace("<Folder>", "")
                folder = folder.replace("</Folder>", "")
                if folder != "": 
                    self.inferenceBucketFolder = folder
        if bucket == "":
            self.inferenceBucket = self.artifactBucket
            self.inferenceBucketFolder = ""

    def changeBucket(self):
        if self.inferenceBucket == self.artifactBucket:
            print()
            print("---------------------------------------")
            print("Enter the desired bucket to be used to store the inference ouput (Leave blank to use the default \"" +
                  self.artifactBucket+")")
            print()
            print("Note: Using a seperate bucket for inference results will allow retention when deleting deployment.")
            print("---------------------------------------")
            usr_input = input("\nBucket Name: ")
            if validate(usr_input):
                if (usr_input != ""):
                    if "/" in usr_input:
                        print("(ERROR) Folders can be declared in the next step of the installer")
                        self.changeBucket()
                    else:
                        self.inferenceBucket = usr_input
                else:
                    self.inferenceBucket = self.artifactBucket
            else:
                self.changeBucket()
        else:
            print()
            print("---------------------------------------")
            print("Enter the desired bucket to be used to store the inference ouput (Leave blank to use the detected bucket \""+self.inferenceBucket+"\")")
            print()
            print("Note: Using a seperate bucket for inference results will allow retention when deleting deployment.")
            print("---------------------------------------")
            usr_input = input("\nBucket Name: ")
            if validate(usr_input):
                if (usr_input != ""):
                    if "/" in usr_input:
                        print("(ERROR) Folders can be declared in the next step of the installer")
                        self.changeBucket()
                    else:
                        self.inferenceBucket = usr_input
            else:
                self.changeBucket()

    def changeFolder(self):
        if self.inferenceBucketFolder == "":
            print()
            print("---------------------------------------")
            print("Enter the desired folder to be used to store the inference ouput i.e. \"folder1/folder2\" (Leave blank to use no folder and store inference results on the top level of the bucket)")
            print("---------------------------------------")
            usr_input = input("\nFolder Name: ")
            if validate(usr_input):
                if (usr_input != ""):
                    self.inferenceBucketFolder = usr_input
                else:
                    self.inferenceBucketFolder == ""
            else:
                self.changeFolder()

        else:
            print()
            print("---------------------------------------")
            print("Enter the desired folder to be used to store the inference ouput i.e. \"folder1/folder2\" (Leave blank to use the detected bucket \""+self.inferenceBucketFolder+"\" or enter \"0\" to use no folder and store inference results on the top level of the bucket)")
            print("---------------------------------------")
            usr_input = input("\nBucket Name: ")
            if (usr_input != ""):
                if (usr_input == 0):
                    self.inferenceBucketFolder = ""
                else:
                    self.inferenceBucketFolder = usr_input
            else:
                self.inferenceBucketFolder == self.inferenceBucketFolder

    def extractInferenceEngine(self):
        inferenceEngine = ""
        with open("./Temp/profiletemp/aws-lookout-vision/adlinkedge/config/AWSLookoutVision.xml") as xmlFile:
            for line in xmlFile.readlines():
                if "<EngineId>" in line:
                    inferenceEngine = line.strip()
        if inferenceEngine != "":
            inferenceEngine = inferenceEngine.replace("<EngineId>", "")
            inferenceEngine = inferenceEngine.replace("</EngineId>", "")
            self.inferenceEngine = inferenceEngine
        else:
            print("(ERROR) An error occured while extracting the inference engine ID from the profile to use for the final node-red configuration, please check your configuration and retry. ")
            self.run()

    def extractConfig(self):
        self.copyProfile()
        self.extractTopic()
        self.extractBucket()
        self.checkForEmpties()
        self.extractInferenceEngine()
        self.changeTopic()
        self.changeBucket()
        self.changeFolder()
        subprocess.check_output(
            ["rm", "-r", "Temp/"])

    def nameInferenceComponent(self):
        print()
        print("---------------------------------------")
        print("Enter the a unique name for the inference component or leave blank to use the default \"" +
              (self.thingName).lower()+".inference.component\"")
        print("---------------------------------------")
        usr_input = input("\nInference Component Name: ")

        self.thingNameLower = self.thingName.lower()

        try:
            if validate(usr_input):
                if (usr_input != ""):
                    self.inferenceComponentName = usr_input
                else:
                    self.inferenceComponentName = self.thingNameLower+".inference.component"
            else:
                self.nameInferenceComponent()
        except:
            return False
        if not self.checkValidComponentName():
            print("(ERROR) Invalid component name already in use")
            self.nameInferenceComponent()
        return True

    def inform(self):
        print("\n---------------------------------------")
        print("Before completing this stage a inference profile created in ADLINK Edge Profile Builder should be exported to this device. Please complete this action before continuing. (See README for more details)")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def informSuccess(self):
        print("\n---------------------------------------")
        print("Inference profile has been successfully deployed, the live results can be witnessed on \"http://localhost:1880/ui\" or via VMLINK and  MQTT messages can be viewed via \"AWS console > Message Broker\" by subscribing to the topic: "+self.topic+".")
        print("---------------------------------------")

    def chooseProfile(self):
        print()
        print("---------------------------------------")
        print("Choose the inference profile from the below options:")
        print("1. aws-lfv-edge-inference template")
        print("2. Custom inference profile")
        print()
        print("---------------------------------------")
        try:
            usr_input = int(input("\nSelect from the options above: "))
            if (usr_input == 1):
                self.pathToProfile = "./templateFiles/profiles/"
                self.profileFile = "aws-lfv-edge-inference.zip"
                self.profileBase = "aws-lfv-edge-inference"
            elif (usr_input == 2):
                self.customInference="True"
                if not self.inform():
                    return False
                self.locateProfile()
            else:
                print("Invalid option provided, please try again.")
        except:
            return False

        return True

    def checkBucketExists(self):
        try:
            existingBucket = subprocess.check_output(
                ["aws", "--profile", self.profileName,"--region", self.awsRegion, "s3api", "head-bucket","--bucket",self.inferenceBucket])
        except subprocess.CalledProcessError as e:
            self.bucketExists = "False"

    def saveDeployment(self):
        session = subprocess.Popen(["./saveDeployment.sh " + self.awsRegion + " " +
                                    "streamer-and-model-and-inference-deployment.json"+ " " + self.stage], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def run(self):
        if not self.chooseProfile():
            return False
        self.extractConfig()
        if not self.nameInferenceComponent():
            return False
        self.checkBucketExists()
        if not self.deployInference():   
            return False
        self.saveDeployment()
        self.informSuccess()

        manager = jsonhelper.JSONManager()
        manager.addCreatedResource("S5P",self.thingName+"-Artifact-Policy-3", "policy",6)
        artifactbucket = manager.getJsonResourceName("S3B")
        manager.addCreatedResource("S5C",self.inferenceComponentName, "component", 6)
        if self.inferenceBucket != artifactbucket:
            manager.addCreatedResource("S5B",self.inferenceBucket, "inferencebucket",6)
        return True
