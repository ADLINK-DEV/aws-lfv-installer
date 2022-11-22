import os
import subprocess
import jsonhelper



class awsConfigurator:
    def __init__(self):
        self.profileName = "default"

    def setupProfile(self):
        print()
        print("---------------------------------------")
        print("Please enter the aws cli profile name you wish to use for this deployment")
        print("Available profiles:")
        available = subprocess.check_output(
            ["aws", "configure", "list-profiles"])
        print(available.strip().decode("utf-8"))
        print()
        print("Note: not entering a profile name will use \"default\", entering a new profile name will require configuration in future steps.")
        print("---------------------------------------")
        usr_input = input("\nProfile Name: ")

        if (usr_input != ""):
            self.profileName = usr_input

        manager = jsonhelper.JSONManager()
        manager.updateAWSState("profileName", self.profileName)

    def configureAws(self):

        print()
        print("---------------------------------------")
        print("Please enter AWS credentials below for profile: "+self.profileName+", if already configured leave blank to use stored values.")
        print("---------------------------------------")
        session = subprocess.Popen(["aws configure --profile " + self.profileName], shell=True, env=os.environ.copy())
        session.communicate()


    def run(self):
        self.setupProfile()
        self.configureAws()
        
        return True
