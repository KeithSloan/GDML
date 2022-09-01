class Assembly:
    def __init__(self, name, ObjList, www, xxx):
        self.name = name
        self.list = ObjList
        self.www = www
        self.xxx = xxx

    def index(self, name):
        idx = 0
        for i in range(len(self.List)):
            obj = self.list[i]
            if obj.Name == name:
                return idx
            if obj.TypeId == "App::Part" or obj.TypeId == "App::Link":
                idx += 1
        return None

    def getPVname(self, name):
        print(f"getPVname {self.name} www {self.www} xxx {self.xxx}")
        print(f"zzz {self.index, name}")
