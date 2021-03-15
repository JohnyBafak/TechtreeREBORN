__version__ = "0.5.4"
UIv = 21
print "[LOADMOD] (aTechTree) v.{}# {}".format(__version__,UIv, "21-03-15")
""" 
 Advanced TechTree by Johny_Bafak
 http://forum.worldoftanks.eu/index.php?/topic/514277-
"""
# Common
import inspect, functools, os, zipfile, urllib
import ResMgr, BigWorld, nations
from gui import SystemMessages

# Mod settings API
from gui.mods.atechtree import g_aTT
    
# Vehicle preview
from gui.shared.gui_items.Vehicle import Vehicle
from items import _xml

# tank comparison
import gui.game_control.veh_comparison_basket
from gui.shared.utils.requesters.ItemsRequester import REQ_CRITERIA

# TechTree
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
from gui.Scaleform.daapi.view.lobby.techtree.techtree_page import TechTree
from gui.Scaleform.daapi.view.lobby.techtree.data import NationTreeData, ResearchItemsData
from gui.Scaleform.genConsts.NODE_STATE_FLAGS import NODE_STATE_FLAGS
import gui.Scaleform.daapi.view.lobby.techtree.settings as SETT
CONFIG = {}
LAYOUTS = []
"""         Common utils:
                @override               override standart function
"""
def override(obj, prop, getter=None, setter=None, deleter=None):
    if inspect.isclass(obj) and prop.startswith('__') and prop not in dir(obj) + dir(type(obj)):
        prop = obj.__name__ + prop
        if not prop.startswith('_'):
            prop = '_' + prop

    src = getattr(obj, prop)
    if type(src) is property and (getter or setter or deleter):
        assert callable(getter) and (setter is None or callable(setter)) and (deleter is None or callable(deleter)), 'Args is not callable!'

        getter = functools.partial(getter, src.fget) if getter else src.fget
        setter = functools.partial(setter, src.fset) if setter else src.fset
        deleter = functools.partial(deleter, src.fdel) if deleter else src.fdel

        setattr(obj, prop, property(getter, setter, deleter))
        return getter
    elif getter:
        assert callable(src), 'Source property is not callable!'
        assert callable(getter), 'Handler is not callable!'

        getter_new = lambda *args, **kwargs: getter(src, *args, **kwargs)
        if not inspect.ismethod(src) and inspect.isclass(obj):
            getter_new = staticmethod(getter_new)

        setattr(obj, prop, getter_new)
        return getter
    else:
        return lambda getter=None, setter=None, deleter=None: override(obj, prop, getter)

"""         Preview for all tanks:
                @gui.share.gui_items.Vehicle.isPreviewAllowed
"""
def isPreviewAllowed(self, x = None):
    """ allow preview for all tank models in game """
    #get vehicle name
    nat, name = self.name.split(':')
    xmlPath = 'scripts/item_defs/vehicles/%s/%s.xml' % (nat, name) 
    ResMgr.purge(xmlPath)    
    section = ResMgr.openSection(xmlPath)
    # generate model name&path
    xmlCtx = (None, xmlPath)
    precessed = _xml.getSubsection(xmlCtx, section, 'hull/models')
    xPath = '{0:>s}/hull/models'.format(xmlPath)
    xmlCtx = (None, xPath)
    modelPath = _xml.readString(xmlCtx, precessed, 'undamaged')
    # check if model exists
    file = ResMgr.openSection(modelPath)
    return True if file is not None and ResMgr.isFile(modelPath) else False
Vehicle.isPreviewAllowed = isPreviewAllowed

"""         Tank comparison extended:
               var gui.game_control.veh_comparison_basket._COMPARE_INVALID_CRITERIA 
               @to-do unlock all parameters
"""
gui.game_control.veh_comparison_basket._COMPARE_INVALID_CRITERIA = ~REQ_CRITERIA.VEHICLE.EVENT_BATTLE

"""         Techtree functionality:
                load all tanks
                update node data for all vehicles
                fix research page crash

"""
class aTechTree():
    
    def __init__(self):
        """ aTechTree main function class """
        
        override(NationTreeData, 'load', self.load)                                     # Add all nodes
        override(NationTreeData, '_makeRealExposedNode', self._makeRealExposedNode)     # Node display info
        override(TechTree, 'goToNextVehicle', self.goToNextVehicle)                     # Reseasch page crash
        # error handle
        import gui.Scaleform.daapi.view.lobby.techtree.techtree_dp as TT_dp
        print TT_dp.TREE_SHARED_REL_FILE_PATH
        TT_dp.TREE_SHARED_REL_FILE_PATH = "../mods/configs/techtree/xml/{}/tree-shared.xml".format( LAYOUTS[ CONFIG.get('layout') ] )
        print TT_dp.TREE_SHARED_REL_FILE_PATH
        override(TT_dp._TechTreeDataProvider,'_TechTreeDataProvider__readNodeLines', self._readNodeLines)
        override(TT_dp._TechTreeDataProvider,'_TechTreeDataProvider__getLineInfo', self._getLineInfo)
        override(TT_dp._TechTreeDataProvider,'_TechTreeDataProvider__readNodeList', self._readNodeList)
        override(TT_dp._TechTreeDataProvider,'_TechTreeDataProvider__readNation', self._readNation)
        #tree-share path
        override(TT_dp._TechTreeDataProvider,'getAvailableNations', self.getAvailableNations)
        override(TT_dp._TechTreeDataProvider,'_TechTreeDataProvider__readDefaultLine', self._readDefaultLine)
    
    def load(hook, baseFunc, self, nationID, override = None):
        """ techtree.data.NationTreeData.load """
        self.clear()
        g_techTreeDP.setOverride(override)
        g_techTreeDP.load()
        getItem = self.getItem
        selectedID = ResearchItemsData.getRootCD()
        unlockStats = self.getUnlockStats()
        for node, displayInfo in g_techTreeDP.getNationTreeIterator(nationID):
            nodeCD = node.nodeCD
            if node.isAnnouncement:
                self._addNode(nodeCD, self._makeAnnouncementNode(node, displayInfo))
            item = getItem(nodeCD)
                
            if item.isOnlyForEventBattles or item.isOnlyForEpicBattles or item.isOnlyForBattleRoyaleBattles or item.isEvent:
                if not CONFIG.get("showEvent"):
                    continue
            elif item.isCollectible:
                if not CONFIG.get("showCollec"): 
                    continue
            elif item.isHidden:
                if not CONFIG.get("showHidden"):
                    continue           
            
            index = self._addNode(nodeCD, self._makeRealExposedNode(node, item, unlockStats, displayInfo))
            if nodeCD == selectedID:
                self._scrollIndex = index

        ResearchItemsData.clearRootCD()
        self._findSelectedNode(nationID)
        if self._scrollIndex < 0:
            self._findActionNode(nationID)
    
    def _makeRealExposedNode(hook, baseFunc, self, node, guiItem, unlockStats, displayInfo):
        """ techtree.data.NationTreeData._makeRealExposedNode """
        data = baseFunc(self, node, guiItem, unlockStats, displayInfo)
        if guiItem.isHidden and not guiItem.isInInventory:
            #scripts\client\gui\Scaleform\genConsts\NODE_STATE_FLAGS.py
            if guiItem.isPremium:
                data.setState(256)  #WAS_IN_BATTLE == no buy button
        return data
        
    def goToNextVehicle(hook, baseFunc, self, vehCD):
        """ techtree.techtree_page.TechTree.goToNextVehicle """
        item = self._data.getItem(int(vehCD))
        if item.isPreviewAllowed():
            baseFunc(self, vehCD)
        
    def _getLineInfo(hook, baseFunc, self, xmlCtx, lineName, nodeCD, outPin, inPin, lineShared):
        """ techtree_dp """
        if CONFIG.get('sysMessage'):
            try:
                res = baseFunc(self, xmlCtx, lineName, nodeCD, outPin, inPin, lineShared)
            except Exception as msg:
                SystemMessages.pushMessage(msg, type=SystemMessages.SM_TYPE.Error)
            return res
            
        else: 
            return baseFunc(self, xmlCtx, lineName, nodeCD, outPin, inPin, lineShared)
            
    def _readNodeLines(hook, baseFunc, self, parentCD, nation, xmlCtx, section, shared):
        """ techtree_dp """
        if CONFIG.get('sysMessage'):
            try:
                lines = baseFunc(self, parentCD, nation, xmlCtx, section, shared)
            except Exception as msg:
                SystemMessages.pushMessage(msg, type=SystemMessages.SM_TYPE.Error)
            return lines
            
        else: 
            return baseFunc(self, parentCD, nation, xmlCtx, section, shared)
            
    def _readNodeList(hook, baseFunc, self, shared, nation, xmlPath, clearCache=False):
        """ techtree_dp """
        if CONFIG.get('sysMessage'):
            try:
                displayInfo, displaySettings, gridSettings = baseFunc(self, shared, nation, xmlPath, clearCache)
            except Exception as msg:
                SystemMessages.pushMessage(msg, type=SystemMessages.SM_TYPE.Error)
            return (displayInfo, displaySettings, gridSettings)
            
        else:
            return baseFunc(self, shared, nation, xmlPath, clearCache)
    
    def _readNation(hook, baseFunc, self, shared, nation, clearCache=False):
        """ techtree_dp """
        try:
            xmlPath = "../mods/configs/techtree/xml/{}/{}-tree.xml".format( LAYOUTS[CONFIG.get('layout')], nation)
            ResMgr.purge(xmlPath)
            displayInfo, displaySettings, gridSettings = self._TechTreeDataProvider__readNodeList(shared, nation, xmlPath, clearCache)
            xmlPath = "../mods/configs/techtree/xml/{}/{}-premium.xml".format( LAYOUTS[CONFIG.get('layout')], nation)
            ResMgr.purge(xmlPath)
            premDisplayInfo, _, gridPremiumSettings = self._TechTreeDataProvider__readNodeList(shared, nation, xmlPath, clearCache)
            nationID = nations.INDICES[nation]
            self._TechTreeDataProvider__displaySettings[nationID] = displaySettings
            self._TechTreeDataProvider__gridSettings[nationID] = gridSettings
            self._TechTreeDataProvider__premiumGridSettings[nationID] = gridPremiumSettings
            displayInfo.update(premDisplayInfo)
            return displayInfo
        except Exception as err:
            print err
            return {}  

    def getAvailableNations(hook, baseFunc, self):  
        """ techtree_dp """
        import gui.Scaleform.daapi.view.lobby.techtree.techtree_dp as TT_dp
        print "getAvailableNations"
        print TT_dp.TREE_SHARED_REL_FILE_PATH
        if self._TechTreeDataProvider__availableNations is None:
            TREE_SHARED = "../mods/configs/techtree/xml/{}/tree-shared.xml".format( LAYOUTS[ CONFIG.get('layout') ] )
            section = ResMgr.openSection(TREE_SHARED)
            if section is None:
                _xml.raiseWrongXml(None, TREE_SHARED, 'can not open or read')
            xmlCtx = (None, TREE_SHARED)
            self._TechTreeDataProvider__availableNations = self._TechTreeDataProvider__readAvailableNations(xmlCtx, section)
        return self._TechTreeDataProvider__availableNations[:]
        
    def _readDefaultLine(hook, baseFunc, self, shared, xmlCtx, section):
        import gui.Scaleform.daapi.view.lobby.techtree.techtree_dp as TT_dp
        print "_readDefaultLine"
        print TT_dp.TREE_SHARED_REL_FILE_PATH
        baseFunc(self, shared, xmlCtx, section)
        return
    
def DB_upd(dbFile):
    try:
        #urllib.urlretrieve ('https://github.com/JohnyBafak/techtreeRelease/raw/main/xml/xml.pkg', dbFile )
        urllib.urlretrieve ('https://bit.ly/3vpK0LK', dbFile )
        print "(aTechTree): Downloading xml.pkg"
        if os.path.isfile( dbFile ):
            with zipfile.ZipFile(dbFile) as zf:
                
                zf.extractall( dbFile[:-4] )  # folder name
            os.remove( dbFile )
        else:
            raise
    except Exception as E: print "[ERROR] (aTechTree): Update failed! (%s)" % E

def DB_check(dbF):
    # lookup available DB version
    try:
        f = urllib.urlopen( "https://raw.githubusercontent.com/JohnyBafak/techtreeRelease/main/xml/db.ver" ) 
        ver = int( f.read() )
    except: ver = 0
    
    # check if local DB excists & download if not
    if not os.path.isfile("mods/configs/techtree/xml/db.ver"):
        print "(aTechTree): No DB.ver file, downloading current db version", ver
        DB_upd(dbF)
        return ver, ver
        
    # lookup local DB version
    with open("mods/configs/techtree/xml/db.ver") as f:
        cur = int( f.read() )
    print "(aTechTree): Checking for database updates: Current #{}; Available #{}".format(cur, ver)

    if ver > cur:
        if CONFIG.get('dataUpdate'):
            print "updating...", CONFIG.get('update')
            DB_upd(dbF)
            cur = ver         
    return cur, ver

def getLayouts():
    data = []
    for name in os.listdir("mods/configs/techtree/xml"):
        if os.path.isfile("mods/configs/techtree/xml/{}/ussr-tree.xml".format(name)):
            data.append(name)
    data.sort()
    return data
    
template  = {
	'modDisplayName': 'Advanced TechTree {ver}-{ui}'.format(ver=__version__, ui=UIv),
	'enabled': True,
    'UIver': UIv,
	'column1': [
        { 'type': "Empty" },
		
		{ 'type': 'CheckBox',   'varName': 'showHidden',    'value': True,  'text': 'Show hidden vehicles in techtree',
		  'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]' },
        { 'type': 'CheckBox',   'varName': 'showCollec',    'value': True,  'text': "Show collector's tanks in techtree",
		  'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]' },
        { 'type': 'CheckBox',   'varName': 'showEvent',     'value': True,  'text': "Show event tanks in techtree",
		  'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]' },
        { 'type': "Empty" },
        { 'type': 'CheckBox',   'varName': 'dataUpdate',    'value': False,  'text': 'Allow techtree data update',
          'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]' }
	],
	'column2': [
        { 'type': "Empty" },
        { 'type': 'Dropdown', 'varName': 'layout',          'value': 1,     'text': 'TechtTree layout',       
          'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]',
		  'width': 400, 'options':  []
		},
        { "varName": "update",   'value': -1,  'type': "RadioButtonGroup", 'text': 'Update data', "options": [ ] },
        { 'type': "Empty" },
		
        { 'type': "Label", 'text': 'Development utils' },
        { 'type': 'CheckBox',   'varName': 'sysMessage',    'value': False,   'text': 'Allow system messages',
          'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]' },   
        { "varName": "reload",   'value': -1,  'type': "RadioButtonGroup", 'text': 'Reload techtree data', "options": [ ], "button": { "width": 200,   "height": 22,   'text': 'Reload' } }
	]
}

def onModSettingsChanged(newSettings):    
    CONFIG.update(newSettings)
    print 'onModSettingsChanged', newSettings
    if 'layout' in newSettings:
        print 'changin Tree-shared XML path'
        import gui.Scaleform.daapi.view.lobby.techtree.techtree_dp as TT_dp
        print TT_dp.TREE_SHARED_REL_FILE_PATH
        TT_dp.TREE_SHARED_REL_FILE_PATH = "../mods/configs/techtree/xml/{}/tree-shared.xml".format( LAYOUTS[ CONFIG.get('layout') ] )
        print TT_dp.TREE_SHARED_REL_FILE_PATH
    
def onButtonClicked(varName, value):    
    print 'onButtonClicked', varName, value
    if varName == "reload":
        g_techTreeDP.load(True)
        if CONFIG.get('sysMessage'):
            SystemMessages.pushMessage("Techtree data has been reloaded.", type=SystemMessages.SM_TYPE.Warning)
        
    elif varName == "update":
        DB_upd('mods/configs/techtree/xml.pkg')
        if g_aTT.TPL["att"]["column2"][2].get('button'):
            g_aTT.TPL["att"]["column2"][2].pop('button', None)
        
        with open("mods/configs/techtree/xml/db.ver") as f: 
            ver = f.read()
            
        g_aTT.TPL["att"]["column2"][2]['text'] = "Current layout data version #{}".format(ver)
        SystemMessages.pushMessage("Database updated to #{}".format(ver), type=SystemMessages.SM_TYPE.Information)

CONFIG = g_aTT.setModTemplate('att', template, onModSettingsChanged, onButtonClicked)  

cur, ver = DB_check('mods/configs/techtree/xml.pkg')
LAYOUTS = getLayouts()

g_aTT.TPL["att"]["column2"][2]['text'] = "Current layout data version #{}".format(cur)
if ver > cur:
    g_aTT.TPL["att"]["column2"][2]['button'] = { "width": 200,   "height": 22,   'text': "Download #{}".format(ver) } 

g_aTT.TPL["att"]["column2"][1]["options"] = [ { 'label': x } for x in LAYOUTS ]


"""print '------------'
for i in dir(TechTree.flashObject):
    print i
    { 'type': 'CheckBox',   'varName': 'autoGap',       'value': True,  'text': 'Automaticaly caltulate gaps',
		  'tooltip': '{HEADER}X{/HEADER}{BODY]s{/BODY]' },
        { 'type': 'RangeSlider','varName': 'gapRange', 'value': [10, 50],   'text': 'Gap size range',
            'divisionLabelPostfix': '', 'divisionLabelStep': 20, 'divisionStep': 20,
			'maximum': 60, 'minimum': 0,	'minRangeDistance': 0,	'snapInterval': 1
		},  
		{ 'type': 'NumericStepper', 'text': 'Gap size range',
			'tooltip': '{HEADER}NumericStepper tooltip header{/HEADER}{BODY}NumericStepper tooltip body{/BODY}',
			'minimum': 1, 'maximum': 15, 'snapInterval': 1,	'value': 5,	'varName': 'numStepperTest'
		},
    
print '------------'"""

g_aTechTree = aTechTree()