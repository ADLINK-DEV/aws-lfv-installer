import os
from os.path import exists
import json
import subprocess
import jsonhelper
import re

def validate(string):
    if re.match(r"^[a-zA-Z0-9-.]*$", string):
        return True
    else:
        print("(ERROR) Chosen model component name / version contains invalid special characters, please use \".\" or \"-\" as seperators if required. ")
        return False


class modelDeployer:
    def __init__(self):
        self.savedState = jsonhelper.JSONManager()
        self.streamerComponentName = self.savedState.getJsonResourceName("S3C")
        self.profileName = self.savedState.getJsonValue(
            "aws_details", "profileName")
        self.awsRegion = self.savedState.getJsonValue(
            "aws_details", "region")
        self.cliVersion = self.savedState.getJsonValue("aws_details", "CliVersion")
        self.modelName = ""
        self.modelVersion = ""
        self.userId = self.savedState.getJsonValue("aws_details", "UserId")
        self.thingName = self.savedState.getJsonResourceName("S2C")
        self.bucketName = self.savedState.getJsonResourceName("S3B")
        self.modelBucket = ""
        self.stage = "5"

    def deployModel(self):
        print("(INFO) Deploying model.")
        session = subprocess.Popen(["./deployModelWithStreamer.sh " + self.profileName + " " + self.awsRegion + " "  + self.modelName + " " +
                                   self.modelVersion + " " + self.streamerComponentName + " " + self.userId + " " + self.thingName + " " + self.modelBucket + " " + self.cliVersion], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def setModelName(self):
        print("\n---------------------------------------")
        print("Enter the component name provided when packaging the model")
        print("---------------------------------------")
        usr_input = input("\nModel Component Name: ")

        try:
            if validate(usr_input):
                if (usr_input != ""):
                    self.modelName = usr_input
                else:
                    print("(ERROR) invalid model component name supplied, please try again")
                    self.setModelName()
            else:
                self.setModelName()
        except:
            return False

        return True

    def setModelVersion(self):
        print("\n---------------------------------------")
        print("Enter the model component version supplied when packaging the model (e.g. \"1.0.0\")")
        print("---------------------------------------")
        usr_input = input("\nModel Version: ")

        try:
            if validate(usr_input):
                if (usr_input != ""):
                    self.modelVersion = usr_input
                else:
                    print("(ERROR) Invalid model version supplied, please try again")
                    self.setModelVersion()
            else:
                self.setModelVersion()
        except:
            return False

        return True

    def modelS3Bucket(self):
        print("(INFO) Getting bucket details from AWS.")
        session = subprocess.Popen(["./getComponent.sh " + self.profileName + " " + self.awsRegion + " " +
                                   self.userId + " " + self.modelName + " " + self.modelVersion], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        
        self.modelBucket = ""
        with open("./Temp/"+self.modelName+"-recipe.json") as recipeFile:
            for line in recipeFile.readlines():
                if "- Uri:" in line:
                    bucketUri = line.strip()
                    bucketUri = bucketUri.replace("- Uri: \"s3://", "")
                    bucketUri = bucketUri.replace(".zip\"", ".zip")
                    self.modelBucket = bucketUri
        
        subprocess.check_output(
            ["rm", "-r", "./Temp"])
        if self.modelBucket == "" :
            print("(ERROR) Unable to detect bucket for model, please ensure model name and version are correct.")
            self.run()
        else:
            return True


    def inform(self):
        print("\n---------------------------------------")
        print("Before completing this stage a model should be trained and packaged for edge deployment using AWS Lookout for Inference.")
        print("\nNOTE: The model component must be exported to an S3 bucket in the same region as the Greengrass Core.")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def saveDeployment(self):
        session = subprocess.Popen(["./saveDeployment.sh " + self.awsRegion + " " +
                                    "streamer-and-model-deployment.json" + " " + self.stage], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def run(self):
        if not self.inform():
            return False
        if not self.setModelName():
            return False
        if not self.setModelVersion():
            return False
        self.modelS3Bucket()
        if not self.deployModel():
            return False
        self.saveDeployment()


        manager = jsonhelper.JSONManager()
        manager.updateAWSState("deployedModelName", self.modelName)
        manager.updateAWSState("deployedModelVersion", self.modelVersion)
        if (self.modelBucket != ""):
            manager.addCreatedResource("S4P",self.thingName+"-Artifact-Policy-2", "policy", 5)
        return True
