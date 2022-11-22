from re import sub
import jsonhelper
import subprocess
import os
import time
import json

class cleanup:
    def __init__(self):
        self.savedState = jsonhelper.JSONManager()
        self.cleanableStages = []
        self.lastDeployed = self.savedState.getLastDeployed()
        self.userId = self.savedState.getJsonValue("aws_details", "UserId")
        self.certID = self.savedState.getJsonValue("aws_details", "certID")
        self.thingName = ""
        self.roleAlias = self.savedState.getJsonValue("aws_details", "thingRoleAlias")
        self.profileName = self.savedState.getJsonValue("aws_details", "profileName")
        self.awsRegion = self.savedState.getJsonValue("aws_details", "region")
        self.localFiles = self.savedState.getLocalFiles()

    def awaitDeploymentStatus(self, targetStatus):
        deployed = False
        while deployed == False:
            activeDeployment = subprocess.check_output(
                ["aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "list-effective-deployments","--core-device-thing-name", self.thingName]).strip().decode("utf-8")
            formatted = json.loads(activeDeployment)
            deployment = formatted["effectiveDeployments"]
            status = deployment[0]["coreDeviceExecutionStatus"]
            if status == targetStatus:
                deployed = True
            else:
                time.sleep(5)

    def deletePolicy(self, policyName):
        print("(INFO) Removing policy: "+ policyName)
        role = self.savedState.getJsonResourceName("S2R")
        # detach from role 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iam", "detach-role-policy", "--role-name", role, "--policy-arn", "arn:aws:iam::"+self.userId+":policy/"+policyName])
        # delete policy 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iam", "delete-policy", "--policy-arn", "arn:aws:iam::"+self.userId+":policy/"+policyName])

    def deleteRole(self, roleName):
        print("(INFO) Removing role:"+ roleName )
        # delete role
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iam", "delete-role", "--role-name", roleName])

    def deleteThingPolicy(self, policyName):
        print("(INFO) Removing thing policy: "+ policyName)
        # detach from certificate 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "detach-policy", "--target", "arn:aws:iot:"+self.awsRegion+":"+self.userId+":cert/"+self.certID, "--policy-name", policyName])
        # delete iot policy 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "delete-policy", "--policy-name", policyName])

    def deleteDeployment(self, deploymentName):
        print("(INFO) Removing deployment: "+deploymentName)
        #get deployment ID
        deploymentIDcontainer = subprocess.check_output(
            ["aws","--region", self.awsRegion, "--profile", self.profileName, "greengrassv2", "list-deployments","--history-filter", "ALL", "--target-arn", "arn:aws:iot:"+self.awsRegion+":"+self.userId+":thing/"+self.thingName]).strip().decode("utf-8")
            
        formatted = json.loads(deploymentIDcontainer)
        deployments = formatted["deployments"]
        # for deployment in deployments
        for deployment in deployments:
            if deployment["deploymentStatus"] == "COMPLETED":
                # cancel active deployment
                subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "cancel-deployment", "--deployment-id", deployment["deploymentId"]])
            # delete deployments
            subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "delete-deployment", "--deployment-id", deployment["deploymentId"]])

    def deleteCore(self, coreName):
        print("(INFO) Removing core: "+coreName)
        # deactivate certificate 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "update-certificate", "--certificate-id", self.certID, "--new-status", "INACTIVE"])
        # detach thing
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "detach-thing-principal", "--thing-name", coreName, "--principal", "arn:aws:iot:"+self.awsRegion+":"+self.userId+":cert/"+self.certID])
        # detach role alias policy
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "detach-policy", "--target", "arn:aws:iot:"+self.awsRegion+":"+self.userId+":cert/"+self.certID, "--policy-name", "GreengrassTESCertificatePolicy"+self.roleAlias ])
        # delete role alias 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "delete-policy", "--policy-name", "GreengrassTESCertificatePolicy"+self.roleAlias ])
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "delete-role-alias", "--role-alias", self.roleAlias ])
        # remove certificate 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "delete-certificate", "--certificate-id", self.certID ])
        # delete core
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "delete-core-device", "--core-device-thing-name", coreName])  
        # delete thing
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "iot", "delete-thing", "--thing-name", coreName])
        # clear local files
        if self.informSudoPermissions():
            session = subprocess.Popen(["sudo ./removeLocalInstall.sh"], shell=True, env=os.environ.copy())
            session.communicate()
            manager = jsonhelper.JSONManager()
            manager.setLocalFiles(False)
        else:
            print("(INFO) Local files and greengrass have not been removed, if a new core is deployed before removing these, duplicates will be created. You can remove the local files and service by revisiting this menu.")

    def deleteComponent(self, componentName):
        print("(INFO) Removing component: "+componentName)
        # delete component 
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "delete-component", "--arn", "arn:aws:greengrass:"+self.awsRegion+":"+self.userId+":components:"+componentName+":versions:1.0.0"])

    def deleteBucket(self, bucketName):
        print("(INFO) Removing bucket: "+bucketName)
        #empty bucket
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "s3", "rm", "s3://"+bucketName, "--recursive"])
        #delete bucket
        subprocess.check_output(["aws", "--profile", self.profileName, "--region", self.awsRegion, "s3api", "delete-bucket", "--bucket", bucketName, "--region", self.awsRegion])

    def confirmInferenceDeletion(self):
        print("\n---------------------------------------")
        print("Would you like to remove the inference results")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def informSudoPermissions(self):
        print()
        print("---------------------------------------")
        print("This stage requires sudo permissions to remove the local greengrass install and greengrass service, if you have not recently provided permission you will be prompted for the sudo password.")
        print("---------------------------------------")
        usr_input = input("\nContinue? (y/n): ")
        if (usr_input == "Y" or usr_input == "y"):
            return True
        else:
            return False

    def deleteStageAssets(self,stage):
        print("(INFO) Delete called for stage: "+str(stage) + " assets.")
        manager = jsonhelper.JSONManager()
        assets = manager.state["created_resources"]
        
        for resource in list(assets):
            asset = manager.state["created_resources"][resource]
            if asset["stage"] == stage:
                assetName = asset["name"]
                if asset["asset_type"] == "policy":
                    self.deletePolicy(assetName)
                elif asset["asset_type"] == "component":
                    self.deleteComponent(assetName)
                elif asset["asset_type"] == "deployment":
                    self.deleteDeployment(assetName)
                elif asset["asset_type"] == "role":
                    self.deleteRole(assetName)
                elif asset["asset_type"] == "bucket":
                    self.deleteBucket(assetName)
                elif asset["asset_type"] == "thingpolicy":
                    self.deleteThingPolicy(assetName)
                elif asset["asset_type"] == "core":
                    self.deleteCore(assetName)
                elif asset["asset_type"] == "inferencebucket":
                    if self.confirmInferenceDeletion():
                        self.deleteBucket(assetName)
                else:
                    return False
                manager.removeCreatedResource(resource)
        manager2 = jsonhelper.JSONManager()
        state = manager2.state["progress"]
        keys_list = list(state)
        manager2.updateState(keys_list[stage-1], False)
        subprocess.check_output(["rm", "templateFiles/deployments/"+str(stage)+"-deployment.json"])
        if stage == 3:
            subprocess.check_output(["rm","-r", "templateFiles/deployments/"])
        return True
    
    def redeployPrevious(self):
        print("(INFO) Redeploying previous configuration from stage: "+str(self.lastDeployed-1))
        subprocess.check_output([ "aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "create-deployment", "--cli-input-json", "file://templateFiles/deployments/"+str(self.lastDeployed-1)+"-deployment.json"])

    def deployEmpty(self):
        subprocess.check_output([ "aws", "--profile", self.profileName, "--region", self.awsRegion, "greengrassv2", "create-deployment", "--cli-input-json", "file://templateFiles/deployments/blank-deployment.json"])
        time.sleep(5)
        self.awaitDeploymentStatus("COMPLETED")

    def displayCleanupMainMenu(self):
        manager = jsonhelper.JSONManager()
        state = manager.state["progress"]
        keys_list = list(state)
        print("---------------------------------------")
        print("Please select from the following options:")
        if self.lastDeployed >= 3:
            print("1: Clean full install (removes all created assets and local greengrass install)")
        elif self.lastDeployed == 2 and self.localFiles == True:
            print("1: Remove local files (requires sudo permissions)")
        else:
            print()
            print("There is nothing to be removed.")
        if self.lastDeployed > 3:
            print("2: Undo last deployed stage: Stage "+str(self.lastDeployed)+ " - " + keys_list[self.lastDeployed-1])
         
        print("0: Exit Cleanup menu")
        print()
        if self.lastDeployed >= 3:
            print("WARNING: Clean full install will remove created AWS resources (deployments, components, policies etc.) and remove the local greengrass install.")
        print("---------------------------------------\n")
        return True
    
    def handleInput(self):
        while True:
            try:
                choice = int(input("Please select from the options above: "))
                if (choice != " " or choice != "") and choice >= 0 and choice < 8:
                    break
                else:
                    print("(ERROR) Invalid option, please try again")
            except ValueError:
                print("(ERROR) choice provided must be a number")
        
        if self.lastDeployed != 1:
            if choice == 1 and self.lastDeployed > 2:
                self.thingName = self.savedState.getJsonResourceName("S2C")
                print("Full deletion requested deploying empty profile")
                self.deployEmpty()
                for x in range(max(self.cleanableStages),2,-1):
                    if x != 0:
                        self.deleteStageAssets(x)
                manager = jsonhelper.JSONManager()
                manager.updateLastDeployedStage(2)
                manager.clearStoredAWSValues()
                return False
            elif choice == 1 and self.lastDeployed == 2:
                session = subprocess.Popen(["sudo ./removeLocalInstall.sh"], shell=True, env=os.environ.copy())
                session.communicate()
                manager = jsonhelper.JSONManager()
                manager.setLocalFiles(False)
                return False

            elif choice == 2 and self.lastDeployed > 2:
                if (self.lastDeployed - 1) in self.cleanableStages:
                    manager = jsonhelper.JSONManager()
                    self.thingName = self.savedState.getJsonResourceName("S2C")
                    if self.lastDeployed > 3:
                        self.redeployPrevious()
                        self.awaitDeploymentStatus("COMPLETED")
                        print("(INFO) Redeployed previous stage")
                    self.deleteStageAssets(self.lastDeployed)
                    
                    state = manager.state["progress"]
                    keys_list = list(state)
                    manager.updateState(keys_list[self.lastDeployed-1], False)
                    manager.updateLastDeployedStage(self.lastDeployed-1)
                    print("(INFO) Stage reverted correctly.")
                    return False
            else:
                return False


            return True
        else:
            print("(INFO) Nothing left to clean. Exiting cleaning menu")

    def detectCleanableStages(self):
        manager = jsonhelper.JSONManager()
        state = manager.state["progress"]
        keys_list = list(state)
        i = 1
        for stage in keys_list:
            if state[stage]["complete"] == True:
                self.cleanableStages.append(i)
            i += 1


    def run(self):
        self.detectCleanableStages()
        while self.displayCleanupMainMenu() == True:
            if self.handleInput() == False:
                return False

        return True
