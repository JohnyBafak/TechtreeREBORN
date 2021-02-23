__version__ = "0.2"
""" 
 TankAvailable by Johny_Bafak
 http://forum.worldoftanks.eu/index.php?/topic/514277-
"""
import ResMgr
import nations
from items import vehicles as vehicles_core

sGetTanks = vehicles_core.VehicleList()

gPath = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2][0].asString

"""def tagClear(data, atr=[], res=[]):
    recursion = overkill
    if len(atr):
        tag = atr[0]
        if tag in data:
            data.remove(tag)
            res.append(True)
        else:
            res.append(False)
        atr.pop(0)
        tagClear(data,atr,res)
    return res, data"""
    
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
    with open(gPath + '_tankList.csv', 'a') as f:
        
        clear = [ "premium", "premiumIGR", "secret", "fallout", "bob", 'collectorVehicle', "HD",
                    'lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG' ] 
        
        for k, v in tanks.iteritems():
            iNat, iNam = v.name.split(":")
            
            vehicleTags = list(v.tags)
            tag, vehicleTags = tagClear(vehicleTags, clear,[])         
            #tag, vehicleTags = tagClear(vehicleTags, [])         
                           
            cls = vehicles_core.getVehicleClassFromVehicleType(v)
            #         1, 2,   3, 4, 5, 6, 7, 8, 9,10,11,12,13
            f.write('{},{},"{}",{},{},{},{},{},{},{},{},{},{},"{}"\n'.format(
                iNat, iNam, v.userString, v.id, v.compactDescr, v.level, cls, tag[0], tag[1], tag[2], tag[3], tag[4], tag[5], vehicleTags) )
            #      1,    2,            3,    4,              5,       6,   7,      8,     9,     10,     11,     12,     13,        14,     
"""
2021-02-13 15:19:09.844: INFO: ['_getDescription', 'clear', 'compactDescr', 'copy', 'description', 'get', 'has_key', 'i18n', 'id',
                                'itemTypeName', 'items', 'keys', 'level', 'longDescriptionSpecial', 'name', 'pop', 
                                'shortDescriptionSpecial', 'shortUserString', 'status', 'tags', 'typeID', 'update', 'userString', 'values']
2021-02-13 15:26:28.717: INFO: france:F20_RenaultBS
2021-02-13 15:26:28.717: INFO: 3
2021-02-13 15:26:28.717: INFO: 0
2021-02-13 15:26:28.717: INFO: 833
2021-02-13 15:26:28.738: INFO: <bound method VehicleItem.has_key of VehicleItem(id=3, name=france:F20_RenaultBS, level=2, status=0)>
2021-02-13 15:26:28.738: INFO: <items.components.shared_components.I18nComponent object at 0x0000000046F36EE8>
2021-02-13 15:26:28.738: INFO: 2
2021-02-13 15:26:28.738: INFO: 
2021-02-13 15:26:28.738: INFO: 
2021-02-13 15:26:28.738: INFO: FT BS
2021-02-13 15:26:28.738: INFO: frozenset(['lightSPG', 'improvedVentilation_class3_user', 'SPG', 'HD', 'collectorVehicle'])
2021-02-13 15:26:28.738: INFO: 1
2021-02-13 15:26:28.738: INFO: Renault FT 75 BS
2021-02-13 15:26:28.739: INFO: <bound method VehicleItem.values of VehicleItem(id=3, name=france:F20_RenaultBS, level=2, status=0)>
"""    
              
print "[MODS] getTanks ", __version__
with open(gPath + '_tankList.csv', 'w') as f:
    f.write('Nation, Name, Userstring, ID, CompID,lvl,class,premium,IGR,hidden,fallout,bob,collectorVehicle,tags\n')

#nationID = 0
for nationID in xrange(len(nations.NAMES)):
    sNationLoad(nationID)