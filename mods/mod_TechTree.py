__version__ = "0.2.2"
""" 
 Advanced TechTree by Johny_Bafak
 http://forum.worldoftanks.eu/index.php?/topic/514277-
 
 Functionality:
    @override 
    preview for all tanks
    unlock comparison
    techtree class
        load all tanks
        set node state
    
    
"""
# Common
import inspect, functools, copy
import ResMgr, BigWorld
from debug_utils import LOG_ERROR, LOG_WARNING, LOG_CURRENT_EXCEPTION
# Mod settings API
try:
    from gui.modsListApi import g_modsListApi
except Exception as E:
    g_modsListApi = None
try:
    VIEW_ALIAS = 'modsSettingsATT' 
    COLUMNS = ('column1', 'column2')
except Exception as E:
    pass
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

"""         Common utils:
                @override               override standart function
"""
def ascii_encode_dict(data):
    ascii_encode = lambda x: str(x) if isinstance(x, unicode) else x
    return dict(map(ascii_encode, pair) for pair in data.items())

def loadView(api):
    ServicesLocator.appLoader.getDefLobbyApp().loadView(SFViewLoadParams(VIEW_ALIAS, VIEW_ALIAS), ctx=api)

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

"""         Tank comparison extended:
               var gui.game_control.veh_comparison_basket._COMPARE_INVALID_CRITERIA 
               @to-do unlock all parameters
"""
gui.game_control.veh_comparison_basket._COMPARE_INVALID_CRITERIA = ~REQ_CRITERIA.VEHICLE.EVENT_BATTLE

"""         Techtree functionality:


"""
class aTechTree():
    
    def __init__(self):
        """ aTechTree main function class """
        override(NationTreeData, 'load', self.load)                                     # Add all nodes
        override(NationTreeData, '_makeRealExposedNode', self._makeRealExposedNode)     # Node display info
        override(TechTree, 'goToNextVehicle', self.goToNextVehicle)                     # Reseasch page crash
    
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
            ##if item.isHidden:
            ##    continue
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
        item = self._data.getItem(int(vehCD))
        print item.isPreviewAllowed()
        if item.isPreviewAllowed():
            baseFunc(self, vehCD)
        
from gui.Scaleform.framework.entities.View import View
from gui.shared.view_helpers.blur_manager import CachedBlur
from frameworks.wulf import WindowLayer
import Event, json
from gui.Scaleform.locale.SETTINGS import SETTINGS
from gui.Scaleform.locale.VEH_COMPARE import VEH_COMPARE
import os, BigWorld
from gui.Scaleform.framework import ScopeTemplates, ViewSettings, g_entitiesFactories
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.shared.personality import ServicesLocator

_preferences_path = os.path.join('mods', 'configs', 'techtree')
if not os.path.exists(_preferences_path): os.makedirs(_preferences_path)
USER_SETTINGS_PATH = os.path.join('mods', 'configs', 'techtree', 'aTechTree.json')

_preferences_path = os.path.dirname(unicode(BigWorld.wg_getPreferencesFilePath(), 'utf-8', errors='ignore'))
if not os.path.exists(_preferences_path): os.makedirs(_preferences_path)
TEMPLATE_PATH = os.path.join(_preferences_path, 'jb_atechtree.dat')

class aUIcontrol():
    def __init__(self):
        self.modList = set()
        self.TPL = {}
        self.CFG = {}
        self.onSettingsChanged = Event.Event()
        self.onButtonClicked = Event.Event()
        self.configLoad()
        
        _info = 'This mod allows you to easily configure installed techtree mods.'
        _png = 'gui/maps/icons/modsSettingsApi/atechtree.png'
        g_modsListApi.addModification('jbATT', "TechTree", _info, _png, True, True, True, functools.partial(loadView, self))
        
    def configLoad(self):
        if os.path.exists(USER_SETTINGS_PATH):
            try:
                with open(USER_SETTINGS_PATH) as f:
                with open(dir + 'AdvancedTechTree.json') as df:
                    for line in f: 
                        file += line.split("//")[0]                 
                    self.CFG = json.loads(file)
            except:
                LOG_WARNING("[aTechTree] Can't load config file, using default settings.")
        
        if os.path.exists(TEMPLATE_PATH):
            try:
                with open(TEMPLATE_PATH) as f:
                    self.TPL = json.load(f, object_hook=ascii_encode_dict)
            except:
                LOG_CURRENT_EXCEPTION()
        else:
            self.TMPsave()
            
    def TMPsave(self):
        try:
            with open(TEMPLATE_PATH, 'w') as f:
                json.dump(self.TPL, f, ensure_ascii=False, encoding='utf-8')
        except:
            LOG_CURRENT_EXCEPTION()
            
    def CFGsave(self):
        try:
            with open(USER_SETTINGS_PATH, 'w') as f:
                f.write("//Advanced TechTree Configuration File\n//GENERATED by in-game settings UI\n")
                json.dump(self.CFG, f, indent=4, separators=(',', ': '))
        except:
            LOG_CURRENT_EXCEPTION()        

    def compareTemplates(self, newTemplate, oldTemplate):
        return newTemplate['UIver'] > oldTemplate['UIver'] if 'UIver' in newTemplate and 'UIver' in oldTemplate else True
        
    def getSettingsFromTemplate(self, template):
        result = dict()
        for column in COLUMNS:
            if column in template:
                result.update(self.getSettingsFromColumn(template[column]))

        if 'enabled' in template:
            result['enabled'] = template['enabled']
        return result
        
    def getSettingsFromColumn(self, column):
        result = dict()
        for elem in column:
            if 'varName' in elem and 'value' in elem:
                result[elem['varName']] = elem['value']

        return result

    def setModTemplate(self, mod, template, callback, buttonHandler=None):
        try:
            self.registerCallback(mod, callback, buttonHandler)
            
            currentTemplate = self.TPL.get(mod)
            if not currentTemplate or self.compareTemplates(template, currentTemplate):
                self.TPL[mod] = template
                self.CFG[mod] = self.getSettingsFromTemplate(template)
                self.TMPsave()
            return self.getModSettings(mod)
        except:
            LOG_CURRENT_EXCEPTION()
        return
        
    def registerCallback(self, mod, callback, buttonHandler=None):
        self.modList.add(mod)
        self.onSettingsChanged += callback
        if buttonHandler is not None:
            self.onButtonClicked += buttonHandler
        return
        
    def getModSettings(self, mod):
        return self.CFG[mod] if mod in self.CFG.keys() else {}
        
    def updateModSettings(self, mod, newSettings):
        self.CFG[mod] = newSettings
        self.onSettingsChanged(mod, newSettings)
        
    def cleanConfig(self):
        for mod in self.TPL.keys():
            if mod not in self.modList:
                del self.TPL[mod]
                del self.CFG[mod]
                
    def getTemplatesForUI(self):
        templates = copy.deepcopy(self.TPL)
        for mod, template in templates.items():
            settings = self.getModSettings(mod)
            template['enabled'] = settings.get('enabled', True)
            for column in COLUMNS:
                if column in template:
                    for component in template[column]:
                        varName = component.get('varName')
                        if varName and settings.get(varName):
                                component['value'] = settings[varName]
        return templates
        
    def genModApiStaticVO(self):
        return {'windowTitle': 'aTechTree mod settings',
        'stateTooltip': '{HEADER}Enable / Disable mod {/HEADER}{BODY} Red indicator - mod disabled <br> Green indicator - mod enabled{/BODY}',
        'buttonOK': SETTINGS.OK_BUTTON,
        'buttonCancel': SETTINGS.CANCEL_BUTTON,
        'buttonApply': SETTINGS.APPLY_BUTTON,
        'buttonClose': VEH_COMPARE.HEADER_CLOSEBTN_LABEL,
        'popupColor': 'COLOR'}
      
class aUIwindow(View):
    def _populate(self):
        super(aUIwindow, self)._populate()
        self._blur = CachedBlur(enabled=True, ownLayer=WindowLayer.OVERLAY - 1)
        global aTTcfg
        aTTcfg.win = self

    def _dispose(self):
        self._blur.fini()
        super(aUIwindow, self)._dispose()
        aTTcfg.CFGsave()

    def sendModsData(self, data):
        data = json.loads(data)
        for linkage in data:
            aTTcfg.updateModSettings(linkage, data[linkage])

    def buttonAction(self, linkage, varName, value):
        aTTcfg.onButtonClicked(linkage, varName, value)
    
    def requestModsData(self):
        aTTcfg.cleanConfig()
        self.as_setStaticDataS(aTTcfg.genModApiStaticVO())
        self.as_setDataS(aTTcfg.getTemplatesForUI())

    def as_setStaticDataS(self, data):
        if self._isDAAPIInited():
            self.flashObject.as_setStaticData(data)

    def as_setDataS(self, data):
        if self._isDAAPIInited():
            self.flashObject.as_setData(data)

    def closeView(self):
        self.destroy()

    def onFocusIn(self, *args):
        return False if self._isDAAPIInited() else None
    


Vehicle.isPreviewAllowed = isPreviewAllowed
aTT = aTechTree()

g_entitiesFactories.addSettings(ViewSettings(VIEW_ALIAS, aUIwindow, 'modsSettingsWindow.swf', WindowLayer.OVERLAY, None, ScopeTemplates.GLOBAL_SCOPE))         
aTTcfg = aUIcontrol()


""" class NODE_STATE_FLAGS(object):
    LOCKED = 1
    NEXT_2_UNLOCK = 2
    UNLOCKED = 4
    ENOUGH_XP = 8
    ENOUGH_MONEY = 16
    IN_INVENTORY = 32
    WAS_IN_BATTLE = 64
    ELITE = 128
    PREMIUM = 256
    SELECTED = 512
    AUTO_UNLOCKED = 1024
    INSTALLED = 2048
    ACTION = 4096
    CAN_SELL = 8192
    VEHICLE_CAN_BE_CHANGED = 16384
    VEHICLE_IN_RENT = 32768
    VEHICLE_RENTAL_IS_OVER = 65536
    PURCHASE_DISABLED = 131072
    RESTORE_AVAILABLE = 262144
    RENT_AVAILABLE = 524288
    DASHED = 1048576
    CAN_TRADE_IN = 2097152
    CAN_TRADE_OFF = 4194304
    NOT_CLICKABLE = 8388608
    ANNOUNCEMENT = 16777216
    BLUEPRINT = 33554432
    LAST_2_BUY = 67108864
    COLLECTIBLE = 134217728
    COLLECTIBLE_ACTION = 268435456
    HAS_TECH_TREE_EVENT = 536870912
    TECH_TREE_EVENT_DISCOUNT_ONLY = 1073741824"""
    

modLinkage = 'att'
UIv = 3
template  = {
	'modDisplayName': 'Advanced TechTree {ver}#{ui}'.format(ver=__version__, ui=UIv),
	'enabled': True,
    'UIv': UIv,
	'column1': [
        { 'type': "Empty" },
		{ 'type': 'CheckBox',   'varName': 'dataUpdate',    'value': False,  'text': 'Allow techtree data update',
          'tooltip': '{HEADER}Показать на миникарте квадрат засвета{/HEADER}{BODY}При вашем обнаружении мод автоматические кликнет на миникарте в квадрат где вы находитесь{/BODY}' },
		{ 'type': 'CheckBox',   'varName': 'sysMessage',    'value': True,   'text': 'Allow system messages',
          'tooltip': '{HEADER}Сообщить в командный чат «Нужна помощь!»{/HEADER}{BODY}При вашем обнаружении мод автоматические отправит команду «Нужна помощь!» вашим союзникам{/BODY}' },   
        { 'type': "Empty" },
		{ 'type': 'CheckBox',   'varName': 'showHidden',    'value': True,  'text': 'Show hidden vehicles in techtree',
		  'tooltip': '{HEADER}Озвучка «Шестого чувства»{/HEADER}{BODY}При срабатывании навыка «Шестого чувства» будет воспроизводиться один из нескольких вариантов озвучки.{/BODY}' },
        { 'type': 'CheckBox',   'varName': 'showCollec',    'value': True,  'text': "Show collector's tanks in techtree",
		  'tooltip': '{HEADER}Озвучка «Шестого чувства»{/HEADER}{BODY}При срабатывании навыка «Шестого чувства» будет воспроизводиться один из нескольких вариантов озвучки.{/BODY}' },
        { 'type': 'CheckBox',   'varName': 'showEvent',     'value': False,  'text': "Show event tanks in techtree",
		  'tooltip': '{HEADER}Озвучка «Шестого чувства»{/HEADER}{BODY}При срабатывании навыка «Шестого чувства» будет воспроизводиться один из нескольких вариантов озвучки.{/BODY}' }
	],
	'column2': [
        { 'type': "Empty" },
        { 'type': 'Dropdown', 'varName': 'layout',          'value': 1,     'text': 'TechtTree layout',       
          'tooltip': '{HEADER}Озвучка «Шестого чувства»{/HEADER}{BODY}При срабатывании навыка «Шестого чувства» будет воспроизводиться один из нескольких вариантов озвучки.{/BODY}',
		  'width': 350, 'options':  [
				{ 'label': 'Wold of Tanks' },
				{ 'label': 'jbDefault' }
			]
		},
        { 'type': "Empty" },
		{ 'type': 'CheckBox',   'varName': 'autoGap',       'value': True,  'text': 'Automaticaly caltulate gaps',
		  'tooltip': '{HEADER}Всегда оповещать о засвете при игре на артиллерии{/HEADER}{BODY}Если вы вишли в бой на артилерии, мод будет всегда оповещать о вашем засвете независимо от выставленного лимита на число оставшехся в живих союзниках{/BODY}' },
        { 'type': 'RangeSlider','varName': 'gapRange', 'value': [10, 50],   'text': 'Gap size range',
			"""'divisionLabelPostfix': '',	'divisionLabelStep': 50, 'divisionStep': 50, """
			'maximum': 100, 'minimum': 0,	'minRangeDistance': 0,	'snapInterval': 1
		},  
		{ 'type': 'NumericStepper', 'text': 'Gap size range',
			'tooltip': '{HEADER}NumericStepper tooltip header{/HEADER}{BODY}NumericStepper tooltip body{/BODY}',
			'minimum': 1, 'maximum': 15, 'snapInterval': 1,	'value': 5,	'varName': 'numStepperTest'
		},
        { "varName": "Reload TechTree",          'type': "RadioButtonGroup", 'text': 'Reload Layout', "options": [ ], "button": { "width": 350,   "height": 22,   'text': 'btn_label' } }
	]
}

def onModSettingsChanged(linkage, newSettings):    
    if linkage == modLinkage:
        print 'onModSettingsChanged', newSettings
    else:
        print 'onModSettingsChanged', linkage, "not meeeeeeeeeeeeeeeee"

def onButtonClicked(linkage, varName, value):    
    if linkage == modLinkage:
        print 'onButtonClicked', linkage, varName, value
    else:
        print 'onButtonClicked', linkage, "not meeeeeeeeeeeeeeeee"


savedSettings = aTTcfg.getModSettings(modLinkage)
if savedSettings:
	settings = savedSettings
	aTTcfg.registerCallback(modLinkage, onModSettingsChanged, onButtonClicked)
else:
	settings = aTTcfg.setModTemplate(modLinkage, template, onModSettingsChanged, onButtonClicked)  