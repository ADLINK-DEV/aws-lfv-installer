import os
import re
import json
import subprocess
import jsonhelper


def validate(string):
    if re.match(r"^[a-zA-Z0-9-]*$", string):
        return True
    else:
        print("(ERROR) Chosen core name contains invalid special characters, please use  \"-\" as a seperator if required. ")
        return False


class deployGreengrassCore:
    def __init__(self):
        self.savedState = jsonhelper.JSONManager()
        self.profileName = self.savedState.getJsonValue(
            "aws_details", "profileName")
        self.localFiles = self.savedState.getLocalFiles()
        self.thingName = ""
        self.awsRegion = ""
        self.thingRole = ""
        self.thingPolicy = ""
        self.thingAlias = ""
        self.userIdNo = 0
        self.certID = ""
        self.stage = "3"
        self.cliVersion = ""

    def informSudoPermissions(self):
        print()
        print("---------------------------------------")
        print("This stage requires sudo permissions to install the greengrass core, if you have not recently provided permission you will be prompted for the sudo password.")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def setupThingName(self):
        print()
        print("---------------------------------------")
        print("Please enter a unique thing name to use for this core deployment")
        print()
        print("Note: Thing names should contain a-z, A-Z, 0-9 and - characters only")
        print("---------------------------------------")
        usr_input = input("\nThing Name: ")
        if validate(usr_input):
            if (usr_input != ""):
                self.thingName = usr_input
                self.thingRole = self.thingName + "-ExchangeRole"
                self.thingPolicy = self.thingName + "-ThingPolicy"
                self.thingAlias = self.thingRole + "-Alias"
            else:
                print("(ERROR) Invalid thing name provided please try again")
                self.setupThingName()
        else:
            self.setupThingName()

    def deployGreengrassCoreToDevice(self):
        session = subprocess.Popen(["./installGreengrassCore.sh " + self.profileName + " " + self.awsRegion + " " +
                                    self.thingName + " " + self.thingRole + " " + self.thingPolicy + " " + self.thingAlias], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def getUserId(self):
        userData = subprocess.check_output(
            ["aws", "--profile", self.profileName, "--region", self.awsRegion, "sts", "get-caller-identity"]).strip().decode("utf-8")
        formatted = json.loads(userData)
        self.userIdNo = formatted["Account"]
    
    def saveCertID(self):
        principals = subprocess.check_output(["aws","--profile", self.profileName, "--region", self.awsRegion, "iot", "list-thing-principals", "--thing-name", self.thingName]).strip().decode("utf-8")
        formatted = json.loads(principals)
        arn = formatted["principals"][0]
        
        seg = arn.split("/")
        self.certID = seg[1]

    def selectRegion(self):
        regions = [["us-east-1", "(US East (N. Virginia))"],
                    ["us-east-2","(US East (Ohio))"],
                    ["us-west-2","(US West (Oregon))"],
                    ["eu-west-1","(Europe (Ireland))"],
                    ["eu-central-1","(Europe (Frankfurt))"],
                    ["ap-northeast-1","(Asia Pacific (Tokyo))"],
                    ["ap-northeast-2","(Asia Pacific (Seoul))"]]
        print()
        print("---------------------------------------")
        print("Choose the AWS region to deploy the core to:")
        i = 1
        for region in regions:
            print(str(i) + ": "+ region[0] + " "+region[1])
            i = i + 1
        print()
        print("Note: The region can differ from the default region specified in configuration stage.")
        print("---------------------------------------")
        try:
            usr_input = int(input("\nSelect from the options above: "))
            if usr_input <= len(regions):
                self.awsRegion = regions[usr_input-1][0]
            else:
                print("Invalid option provided, please try again.")
                self.selectRegion()
        except KeyboardInterrupt:
            return False
        except:
            print("Invalid option provided, please try again.")
            self.selectRegion()

        return True

    def saveDeployment(self):
        self.getUserId()
        session = subprocess.Popen(["./saveDeployment.sh " + self.awsRegion + " " +
                                    "core-only-deployment.json" + " " + self.stage + " " + self.thingName + " " + self.userIdNo + " " + self.cliVersion], shell=True, env=os.environ.copy())
        session.communicate()
        if session.returncode != 0:
            return False
        return True

    def warnDuplicates(self):
        print()
        print("---------------------------------------")
        print("The local files from previous core deployments on this device have not been removed, you can remove these by using option 7 in the main menu. If not removed before deploying another core duplicate cores may be created on the AWS console.")
        print("---------------------------------------")
        usr_input = input("\nContinue with core install? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def run(self):
        if self.localFiles:
            if not self.warnDuplicates():
                return False
        if not self.informSudoPermissions():
            return False
        self.setupThingName()
        if not self.selectRegion():
            return False
        if not self.deployGreengrassCoreToDevice():
            return False
        self.saveCertID()
        self.saveDeployment()
        manager = jsonhelper.JSONManager()
        manager.updateAWSState("thingName", self.thingName)
        manager.updateAWSState("thingRole", self.thingRole)
        manager.updateAWSState("thingPolicy", self.thingPolicy)
        manager.updateAWSState("thingRoleAlias", self.thingAlias)
        manager.updateAWSState("UserId", self.userIdNo)
        manager.updateAWSState("certID", self.certID)
        manager.updateAWSState("region", self.awsRegion)
        manager.setLocalFiles(True)
        manager.addCreatedResource("S2C",self.thingName, "core", 3)
        manager.addCreatedResource("S2D","deployment for "+self.thingName, "deployment", 3)
        manager.addCreatedResource("S2R",self.thingRole, "role", 3)
        manager.addCreatedResource("S2P",self.thingRole+"Access", "policy",3)
        manager.addCreatedResource("S2TP",self.thingPolicy, "thingpolicy",3)
        
        return True
