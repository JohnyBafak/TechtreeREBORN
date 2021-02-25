__version__ = "0.1.1"
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
import inspect, functools
import ResMgr
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
        
         
Vehicle.isPreviewAllowed = isPreviewAllowed
aTT = aTechTree()

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