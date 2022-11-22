import sys
import os
import signal
import deployGreengrassCore
import jsonhelper
import prequisiteInstaller
import installStreamerProfile
import modelDeployer
import inferenceProfileDeployer
import AWScleanup
import configureAWS


def checkPermissions():
    if os.geteuid() != 0:
        print ("(INFO) This installer may ask for sudo permissions to perform certain actions.")
        return True
    else:
        print("(ERROR) This installer should be run without sudo, please try again.")
        return False


def checkRequirements(stage):
    manager = jsonhelper.JSONManager()
    state = manager.state["progress"]
    keys_list = list(state)
    requirements = state[stage]["requirements"]
    requirementsMet = True
    for requirement in requirements:
        if state[keys_list[requirement]]["complete"] == False:
            requirementsMet = False
    return requirementsMet


def handleChoice(choice, installer):
    managerInst1 = jsonhelper.JSONManager()
    state = managerInst1.state["progress"]
    keys_list = list(state)
    if state[keys_list[choice-1]]["complete"] == False or choice == 2:
        if installer.run() == True:
            print("Stage: \""+keys_list[choice-1]+"\" completed succesfully")
            managerInst2 = jsonhelper.JSONManager()
            managerInst2.updateLastDeployedStage(choice)
            managerInst2.updateState(keys_list[choice-1], True)
        else:
            print(
                "An error occurred when completing stage: \""+keys_list[choice-1]+"\", please try again.")
            return False
    else:
        print("Stage: \""+keys_list[choice-1] +
                "\" has already been completed please select again.")


def displayMenu():
    manager = jsonhelper.JSONManager()
    state = manager.state["progress"]
    print()
    print("---------------------------------------")
    keys_list = list(state)
    i = 0
    for stage in keys_list:
        if state[stage]["complete"] == True and i == 1:
            print(str(i+1) + ": " + "--(Configured)-- Reconfigure AWS CLI")
        elif state[stage]["complete"] == True:
            print(str(i+1) + ": " + "--(Complete)-- " + stage)
        elif checkRequirements(stage) == False:
            print(str(i+1) + ": " + "--(Requirements not met)-- " + stage)
        else:
            print(str(i+1) + ": " + stage)
        i += 1
    print("0: Exit Application")
    print("---------------------------------------\n")
    return True


def handleInput():

    while True:
        try:
            choice = int(input("Please select from the options above: "))
            if (choice != " " or choice != "") and choice >= 0 and choice < 8:
                break
            else:
                print("(ERROR) Invalid option, please try again")
        except ValueError:
            print("(ERROR) choice provided must be a number")

    managerInst1 = jsonhelper.JSONManager()
    state = managerInst1.state["progress"]
    keys_list = list(state)
    if choice > 0 and choice < 8:
        if checkRequirements(keys_list[choice-1]) == True:
            if choice == 1:
                prereqInstaller = prequisiteInstaller.prerequisiteInstaller()
                handleChoice(choice, prereqInstaller)

            elif choice == 2:
                awsDetails = configureAWS.awsConfigurator()
                handleChoice(choice, awsDetails)

            elif choice == 3:
                deploygreengrass = deployGreengrassCore.deployGreengrassCore()
                handleChoice(choice, deploygreengrass)

            elif choice == 4:
                installStreamer = installStreamerProfile.installStreamerProfile()
                handleChoice(choice, installStreamer)

            elif choice == 5:
                deployModel = modelDeployer.modelDeployer()
                handleChoice(choice, deployModel)

            elif choice == 6:
                deployInference = inferenceProfileDeployer.inferenceProfileDeployer()
                handleChoice(choice, deployInference)

            elif choice == 7:
                    cleanup = AWScleanup.cleanup()
                    if cleanup.run() == True:
                        print ("(INFO) Cleanup completed")
                    else:
                        print ("(INFO) Cleanup exited")

        else:
                print("Requirements not met, please try again.")

    else:
        return False
    
    return True


def main():
    print("###########################################################")
    print("Welcome to the ADLINK Lookout for Vision Solution Installer")
    print("###########################################################")
    print()

    if not checkPermissions():
        return 1

    while displayMenu() == True:
        if handleInput() == False:
            return 0


if __name__ == "__main__":
    sys.exit(main())
