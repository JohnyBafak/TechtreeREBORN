__version__ = "0.3.1"

import ResMgr
import nations
from items import vehicles as vehicles_core
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
from gui.Scaleform.daapi.view.lobby.techtree.data import NationTreeData
from gui.Scaleform.daapi.view.lobby.techtree import dumpers

sGetTanks = vehicles_core.VehicleList()
gPath = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2][0].asString
    
def tagClear(data, atr=[], res=[]):
    for i in atr:
        if i in data:
            data.remove(i)
            res.append(True)
        else:
            res.append(False)
    return res, data
          
def sNationLoad(natID):
    tanks = sGetTanks.getList(natID)
    g_techTreeDP.load()
    b = NationTreeData(dumpers.NationObjDumper())
    with open(gPath + '_tankList.csv', 'a') as f:
        
        clear = [ "premium", "premiumIGR", "secret", "fallout", "bob", 'collectorVehicle', "HD",
                    'lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG' ] 
        
        for k, v in tanks.iteritems():
            iNat, iNam = v.name.split(":")
            
            item = b.getItem(v.compactDescr)
            
            # helper vehicle:
            if v.compactDescr == 3585: #su-100
                print item.chassis
                print item._chassis
                print item.getBuyPrice
            
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
           
        print "-------------------------------------------------"


print "[MODS] getTanks ", __version__        
try:
        pass
except Exception as Err:
        pass
              
if True:
    with open(gPath + '_tankList.csv', 'w') as f:
        f.write('Nation,Name,Userstring,ID,CompID,lvl,class,premium,IGR,hidden,fallout,bob,collectorVehicle,isOnlyForEventBattles,isOnlyForEpicBattles,isOnlyForBattleRoyaleBattles,isEvent,price,tags\n')

    for nationID in xrange(len(nations.NAMES)):
        sNationLoad(nationID)