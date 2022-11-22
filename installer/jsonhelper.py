import json


class JSONManager:
    def __init__(self):
        self.state = self.loadJSON()

    def loadJSON(self):
        f = open("./config/config.json")
        self.state = json.load(f)
        f.close()
        return self.state

    def updateState(self, target, value):
        self.state["progress"][target]["complete"] = value
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def updateAWSState(self, target, value):
        self.state["aws_details"][target] = value
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def updateProfileConfiguration(self, target, value):
        self.state["profile_configuration"][target] = value
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def addCreatedResource(self,ref, value, asset_type, stage):
        newEntry = { ref : {"name":value, "asset_type": asset_type, "stage":stage}}
        newEntry.update(self.state["created_resources"])
        self.state["created_resources"] = newEntry
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def addCreatedResourceOld(self, target, value):
        self.state["created_resources"][target] = value
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def updateLastDeployedStage(self,value):
        self.state["last deployed stage"] = value
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def setLocalFiles(self,value):
        self.state["local files"] = value
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def removeCreatedResource(self,resource):
        del self.state["created_resources"][resource]
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()

    def clearStoredAWSValues(self):
        for entry in self.state["aws_details"]:
            if entry != "profileName":
                self.state["aws_details"][entry] = ""

        self.state["profile_configuration"]["streamId"] = ""
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)
            f.close()
        self.state = self.loadJSON()

    def getStageName(self,value):
        return self.state["progress"][value].values()

    def getLastDeployed(self):
        return self.state["last deployed stage"]

    def getLocalFiles(self):
        return self.state["local files"]

    def getJsonValue(self, section, target):
        return self.state[section][target]

    def getJsonResourceName(self, target):
        return self.state["created_resources"][target]["name"]
