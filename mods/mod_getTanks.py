__version__ = "0.5.1"
print "[LOADMOD] (aTechTree) getTanks v.{} {}".format(__version__, "21-03-15")

import ResMgr, nations, os
from items import vehicles as vehicles_core
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
from gui.Scaleform.daapi.view.lobby.techtree.data import NationTreeData
from gui.Scaleform.daapi.view.lobby.techtree import dumpers
PATH = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2][1].asString
CONFIG = {}

from gui import SystemMessages
    
def tagClear(data, atr=[], res=[]):
    for i in atr:
        if i in data:
            data.remove(i)
            res.append(True)
        else:
            res.append(False)
    return res, data
          
def gtNationLoad(natID, veh, path, ignore = []):
    print "[NOTE] (getTanks): Loading nation", natID, nations[natID]
    tanks = veh.getList(natID)
    num = 0
    g_techTreeDP.load()
    b = NationTreeData(dumpers.NationObjDumper())
    with open(path + '_tankList.csv', 'a') as f:
        
        clear = [ "premium", "premiumIGR", "secret", "fallout", "bob", 'collectorVehicle', "HD",
                    'lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG' ] 
        
        for k, v in tanks.iteritems():
            tname = v.name
            if tname in ignore:
                msg = 'Skipping tank: {}'.format( tname )
                print '(aTechTree) getTanks: ',msg
                SystemMessages.pushMessage(msg, type=SystemMessages.SM_TYPE.Warning)
                continue
                
            iNat, iNam = tname.split(":")
            item = b.getItem(v.compactDescr)
            
            # helper vehicle:
            """if v.compactDescr == 3585: #su-100
                print dir( item.buyPrices ) 
                print item.buyPrices.itemPrice
                print type(item.buyPrices.itemPrice)"""
                
            vehicleTags = list(v.tags)
            tag, vehicleTags = tagClear(vehicleTags, clear,[])         
                       
            cls = vehicles_core.getVehicleClassFromVehicleType(v)

            f.write('{},{},"{}",{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}"{}"\n'.format(
                iNat, 
                iNam, 
                v.userString, 
                v.id,
                v.compactDescr,
                v.level,
                cls,
                tag[0],
                tag[1],
                tag[2],
                tag[3],
                tag[4],
                tag[5],
                item.isOnlyForEventBattles,
                item.isOnlyForEpicBattles,
                item.isOnlyForBattleRoyaleBattles,
                item.isEvent,
                item.getBuyPrice,
                vehicleTags  ) )
            num +=1
    return num

                
def readIgnore():
    res = list()
    path = os.path.join('mods', 'configs', 'techtree', 'ignoreList.txt')
    if os.path.isfile(path):
        with open(path, 'r') as f:
            line = f.readline().rstrip()
            if len(line) and ":" in line:
                res.append(line)
    return res   

def updateTemplate():
    global g_aTT
    g_aTT.TPL["gtl"]["column1"][1]["options"] = [ { 'label': n } for n in readIgnore() ]
    g_aTT.TPL["gtl"]["column2"][3]["text"] = "Last generated for: {}".format(PATH.rpartition('/')[2]) if os.path.isfile(PATH + "_tankList.csv") else "Not generated yet"    

def startList():
    print "[NOTE] (getTanks): Loading vehicle list from game"
    vehList = vehicles_core.VehicleList()
    tankIgnore = readIgnore()
    count = 0
    
    with open(PATH + '_tankList.csv', 'w') as f:
        f.write('Nation,Name,Userstring,ID,CompID,lvl,class,premium,IGR,hidden,fallout,bob,collectorVehicle,isOnlyForEventBattles,isOnlyForEpicBattles,isOnlyForBattleRoyaleBattles,isEvent,price,tags\n')

    for i, nation in enumerate(nations.NAMES):
        ignore = list()
        if CONFIG.get('ignore'):
            ignore=[k for k in tankIgnore if nation in k]
        count += gtNationLoad(i, vehList, PATH, ignore)
    print "[NOTE] (getTanks): Vehicle list created, found {} tanks".format(count)
    return count

def onGTSettings(newSettings):    
    CONFIG.update(newSettings)
    
def onGTButton(varName, value):    
    count = startList()
    updateTemplate()
    SystemMessages.pushMessage('getVehicle: found {}'.format(count), type=SystemMessages.SM_TYPE.Warning)
    
    

g_aTT = None
try: from gui.mods.atechtree import g_aTT
except Exception as Err: "... no techtree module"
if g_aTT:
    CONFIG  = {
            'modDisplayName': 'GetTanks {ver}'.format(ver=__version__),
            'enabled': True,
            'UIver': 51,
            'column1': [ 
                { 'type': 'CheckBox',   'varName': 'ignore', 'value': False,  'text': 'Ignore vehicles specified in ignoreList',
                'tooltip': '{HEADER}Heade{/HEADER}{BODY}body{/BODY}' },
                { 'type': 'Dropdown', 'varName': 'list', 'value': -1,     'text': 'List of currently ignored vehicles',       
                    'tooltip': '{HEADER}Ignore Vehicle List{/HEADER}{BODY}Specify ignored tanks in ingoreVehicle.txt located in ./mods/configs/techtree folder.\nEach vehicle in list have to follow <nation:vehicle> format.{/BODY}',
                    'width': 400, 'options':  [] 
                },
                
            ],
            'column2': [
                { 'type': 'CheckBox',   'varName': 'vehList', 'value': False,  'text': 'Generate new list on start-up',
                    'tooltip': '{HEADER}Heade{/HEADER}{BODY}body{/BODY}' },
                { 'type': 'Empty' },
                { 'type': 'Empty' },
                { "varName": "reload",   'value': -1,  'type': "RadioButtonGroup", 'text': 'Generate vehicle list', "options": [ ], "button": { "width": 200,   "height": 22,   'text': 'Export Data' }
                }
            ]
    }
    CONFIG = g_aTT.setModTemplate('gtl', CONFIG, onGTSettings, onGTButton)  
    
    updateTemplate()
    
if CONFIG.get('vehList'):
    startList()