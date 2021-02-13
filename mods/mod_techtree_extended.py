# -*- coding: utf-8 -*-
import gui.game_control.veh_comparison_basket
import BigWorld, json, traceback, ResMgr
from helpers import getClientLanguage
from constants import DEFAULT_LANGUAGE
from gui.shared.economics import getGUIPrice
from ResMgr import openSection as _openSection
from gui.shared.gui_items.Vehicle import Vehicle
from gui.shop import canBuyGoldForItemThroughWeb
from gui.Scaleform.daapi.view.lobby.techtree import nodes
from BigWorld import wg_getProductVersion as _productVersion
from gui.shared.utils.requesters.ItemsRequester import REQ_CRITERIA
from gui.Scaleform.genConsts.NODE_STATE_FLAGS import NODE_STATE_FLAGS
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
from gui.Scaleform.daapi.view.lobby.techtree.data import NationTreeData, ResearchItemsData
    
isImportOK = True
try:
    from gui.oldskool import g_modSettings
    from gui.oldskool.utils import hook
except ImportError:
    print '[mod_TechTree]: Mod disabled. Missing modsCore from OldSkool.'
    isImportOK = False
except StandardError:
    traceback.print_exc()
    
##########################################################################################################################################
##########################################################################################################################################
        
class MI():
        
    def __init__(self):
        title = 'Extended TechTree'
        version = '1.1.1'
        date = '13.08.2020'
        author = 'OldSkool'
        print '[LOADMOD] (%s): v.%s (%s) by %s' % (title, version, date, author)
        
##########################################################################################################################################
##########################################################################################################################################
    
class ML():
    
    def __init__(self):
        self.LANGUAGE_CODES = ('ru', 'uk', 'be', 'en', 'de', 'et', 'bg', 'da', 'fi', 'fil', 'fr', 'el', 'hu', 'id',
        'it', 'ja', 'ms', 'nl', 'no', 'pl', 'pt', 'pt_br', 'ro', 'sr', 'vi', 'zh_sg', 'zh_tw', 'hr', 'th',
        'lv', 'lt', 'cs', 'es_ar', 'tr', 'zh_cn', 'es', 'kk', 'sv', )
        
        self.LANGUAGE_FILE_PATH = 'mods/oldskool.techtree/text/%s.yml'
        self.DEFAULT_UI_LANGUAGE = 'en'
        self._LANGUAGES = {}
        
        for langCode in self.LANGUAGE_CODES:
            self._LANGUAGES[langCode] = self.parseLangFields(self.LANGUAGE_FILE_PATH % langCode)
            
        self._CLIENT_LANGUAGE = getClientLanguage()
        if self._CLIENT_LANGUAGE in self._LANGUAGES.keys():
            self._LANGUAGE = self._LANGUAGES[self._CLIENT_LANGUAGE]
        
        elif DEFAULT_LANGUAGE in self._LANGUAGES.keys():
            self._LANGUAGE = self._LANGUAGES[DEFAULT_LANGUAGE]
        else:
            self._LANGUAGE = self._LANGUAGES[self.DEFAULT_UI_LANGUAGE]
        
    def parseLangFields(self, langFile):
        result = {}
        langData = self.readFromVFS(langFile)
        if langData:
            for item in langData.splitlines():
                if ': ' not in item:
                    continue
                key, value = item.split(": ", 1)
                result[key] = value
        return result
        
    def readFromVFS(self, path):
        fileInst = ResMgr.openSection(path)
        if fileInst is not None and ResMgr.isFile(path):
            return str(fileInst.asBinary)
        return None
        
    def l10n(self, key):
        result = key
        if key in self._LANGUAGE:
            result = self._LANGUAGE[key]
        elif key in self._LANGUAGES[self.DEFAULT_UI_LANGUAGE]:
            result = self._LANGUAGES[self.DEFAULT_UI_LANGUAGE][key]
        return result
        
##########################################################################################################################################
##########################################################################################################################################
    
class TechTree():
    
    def __init__(self):
        if g_CFG.config['enabled']:
            g_hook.OVERRIDE(NationTreeData, 'load')(self.__hooked_NationTreeData_load)
            g_hook.OVERRIDE(NationTreeData, '_makeRealExposedNode')(self.__hooked_NationTreeData_makeRealExposedNode)
            g_hook.OVERRIDE(Vehicle, 'isPreviewAllowed')(self.__hooked_Vehicle_isPreviewAllowed)
                
            if g_CFG.config['unlockCompareList']:
                gui.game_control.veh_comparison_basket._COMPARE_INVALID_CRITERIA = ~REQ_CRITERIA.VEHICLE.EVENT_BATTLE
                
    def __hooked_NationTreeData_makeRealExposedNode(self, baseMethod, baseObject, node, guiItem, unlockStats, displayInfo):
        nodeCD = node.nodeCD
        earnedXP = unlockStats.getVehXP(nodeCD)
        state = NODE_STATE_FLAGS.LOCKED
        
        available, unlockProps = g_techTreeDP.isNext2Unlock(nodeCD, level=guiItem.level, **unlockStats._asdict())
        
        if guiItem.isUnlocked:
            state = NODE_STATE_FLAGS.UNLOCKED
            
            if guiItem.isInInventory:
                state |= NODE_STATE_FLAGS.IN_INVENTORY
                if baseObject._canSell(nodeCD):
                    state |= NODE_STATE_FLAGS.CAN_SELL
            else:
                if canBuyGoldForItemThroughWeb(nodeCD) or baseObject._mayObtainForMoney(nodeCD):
                    state |= NODE_STATE_FLAGS.ENOUGH_MONEY
                if baseObject._isLastUnlocked(nodeCD):
                    state |= NODE_STATE_FLAGS.LAST_2_BUY
            if nodeCD in baseObject._wereInBattle:
                state |= NODE_STATE_FLAGS.WAS_IN_BATTLE
            if guiItem.buyPrices.itemPrice.isActionPrice() and not guiItem.isRestorePossible():
                state |= NODE_STATE_FLAGS.ACTION
        else:
            if available:
                state = NODE_STATE_FLAGS.NEXT_2_UNLOCK
                if g_techTreeDP.getAllVehiclePossibleXP(unlockProps.parentID, unlockStats) >= unlockProps.xpCost:
                    state |= NODE_STATE_FLAGS.ENOUGH_XP
            else:
                state = NODE_STATE_FLAGS.PREMIUM
                
            if unlockProps.discount:
                state |= NODE_STATE_FLAGS.ACTION
        if guiItem.isElite:
            state |= NODE_STATE_FLAGS.ELITE
            
        if guiItem.isPremium:
            state |= NODE_STATE_FLAGS.PREMIUM
            
        if guiItem.isRented and not guiItem.isPremiumIGR:
            state = baseObject._checkExpiredRent(state, guiItem)
            state = baseObject._checkMoney(state, nodeCD)
            
        if guiItem.isRentable and not guiItem.isInInventory:
            state = baseObject._checkMoney(state, nodeCD)
        
        if guiItem.isHidden and not guiItem.isInInventory:
            state = NODE_STATE_FLAGS.LOCKED
        
        if baseObject._isVehicleCanBeChanged():
            state |= NODE_STATE_FLAGS.VEHICLE_CAN_BE_CHANGED
        bpfProps = baseObject._getBlueprintsProps(node.nodeCD, guiItem.level)
        
        if bpfProps is not None and bpfProps.totalCount > 0:
            state |= NODE_STATE_FLAGS.BLUEPRINT
        
        state = baseObject._checkRestoreState(state, guiItem)
        state = baseObject._checkRentableState(state, guiItem)
        state = baseObject._checkTradeInState(state, guiItem)
        state = baseObject._checkTechTreeEvents(state, guiItem, unlockProps)
        
        price = getGUIPrice(guiItem, baseObject._stats.money, baseObject._items.shop.exchangeRate)
        
        return nodes.RealNode(node.nodeCD, guiItem, earnedXP, state, displayInfo, unlockProps=unlockProps, bpfProps=bpfProps, price=price)
            
    def __hooked_Vehicle_isPreviewAllowed(self, baseMethod, baseObject, x=None):
        from items import _xml
        nat, tank = baseObject.name.split(':')
        xmlPath = 'scripts/item_defs/vehicles/%s/%s.xml' % (nat, tank)
        ResMgr.purge(xmlPath)
        section = ResMgr.openSection(xmlPath)
        xmlCtx = (None, xmlPath)
        precessed = _xml.getSubsection(xmlCtx, section, 'hull/models')
        xPath = '{0:>s}/hull/models'.format(xmlPath)
        xmlCtx = (None, xPath)
        modelPath = _xml.readString(xmlCtx, precessed, 'undamaged')
        file = ResMgr.openSection(modelPath)
        return True if file is not None and ResMgr.isFile(modelPath) else False
        
    def __hooked_NationTreeData_load(self, baseMethod, baseObject, nationID, override=None):
        baseObject.clear()
        g_techTreeDP.setOverride(override)
        g_techTreeDP.load()
        
        sRem = g_CFG.config['showRemovedTanks']
        sHid = g_CFG.config['showHiddenTanks']
        
        getItem = baseObject.getItem
        selectedID = ResearchItemsData.getRootCD()
        unlockStats = baseObject.getUnlockStats()
        
        removedTanks = ['germany:G04_PzVI_Tiger_IA',
            'germany:G16_PzVIB_Tiger_II_training',
            'germany:G10_PzIII_AusfJ_training',
            'germany:Env_Artillery',
            'germany:G03_PzV_Panther_training',
            'germany:G85_Auf_Panther',
            'germany:G79_Pz_IV_AusfGH',
            'germany:G119_Panzer58',
            'germany:G98_Waffentrager_E100',
            'germany:G120_M41_90',
            'china:Ch04_T34_1_training',
            'china:Ch01_Type59_Gold',
            'uk:GB70_FV4202_105',
            'usa:A08_T23',
            'usa:Sexton_I',
            'usa:A26_T18',
            'usa:A06_M4A3E8_Sherman_training',
            'usa:A15_T57',
            'ussr:Observer',
            'ussr:R70_T_50_2',
            'ussr:R70_T_50_2',
            'ussr:R05_KV']
            
        for node, displayInfo in g_techTreeDP.getNationTreeIterator(nationID):
            nodeCD = node.nodeCD
            if node.isAnnouncement:
                baseObject._addNode(nodeCD, baseObject._makeAnnouncementNode(node, displayInfo))
            else:
                item = getItem(nodeCD)
                if item.isHidden:
                    if item.name in removedTanks:
                        if not sRem:
                            continue
                    elif not sHid:
                        continue
                    
                index = baseObject._addNode(nodeCD, baseObject._makeRealExposedNode(node, item, unlockStats, displayInfo))
                if nodeCD == selectedID:
                    baseObject._scrollIndex = index

        ResearchItemsData.clearRootCD()
        baseObject._findSelectedNode(nationID)

        if baseObject._scrollIndex < 0:
            baseObject._findActionNode(nationID)
    
##########################################################################################################################################
##########################################################################################################################################
        
class CFG():
    
    def __init__(self):
        g_modSettings.onModsDataRequested += self.onModsDataRequested
        g_modSettings.onModsDataSend += self.onModsDataSend
        
        self.modID = 'extendedTechTree'
        self.configPath = 'mods/configs/oldskool/techtree.json'
        self.configVersion = 1
        
        self.doConfig()
        
    def onModsDataRequested(self):
        g_modSettings.setModTemplate(self.modID, self.modTemplate())
        
    def onModsDataSend(self):
        for linkage in g_modSettings.config['settings']:
            if linkage == self.modID:
                self.config = g_modSettings.config['settings'][linkage]
        
    def doConfig(self):
        self.configDefault = {'enabled': True, 'showHiddenTanks': True, 'showRemovedTanks': True, 'unlockCompareList': True}
        
        try:
            with open(self.configPath) as dataFile:
                self.config = json.load(dataFile)
                dataFile.close()
        except ValueError:
            with open(self.configPath, 'w') as dataFile:
                print '[mod_TechTree]: Missing or corrupted configuration. Creating new file..'
                json.dump(self.configDefault, dataFile, sort_keys=False, indent=4, separators=(',', ': '))
                dataFile.close()
                self.config = self.configDefault
                
        if self.config is not None:
            try:
                configVersion = self.config['configVersion']
            except KeyError:
                configVersion = 0
            if configVersion < self.configVersion:
                with open(self.configPath, 'w') as dataFile:
                    print '[mod_TechTree]: Outdated Configuration. Updating file..'
                    json.dump(self.configDefault, dataFile, sort_keys=False, indent=4, separators=(',', ': '))
                    dataFile.close()
                    self.config = self.configDefault
            
    def modTemplate(self):
        return {'column1': [
                    
                    {'type': 'CheckBox',
                    'text': g_ML.l10n('showHiddenTanksLabel'),
                    'tooltip': g_ML.l10n('showHiddenTanksDescription'),
                    'value': self.config['showHiddenTanks'],
                    'varName': 'showHiddenTanks'
                    },
                    
                    {'type': 'CheckBox',
                    'text': g_ML.l10n('showRemovedTanksLabel'),
                    'tooltip': g_ML.l10n('showRemovedTanksDescription'),
                    'value': self.config['showRemovedTanks'],
                    'varName': 'showRemovedTanks'
                    }
                    
                ],
                
                'column2': [
                
                    {'type': 'CheckBox',
                    'text': g_ML.l10n('unlockCompareListLabel'),
                    'tooltip': g_ML.l10n('unlockCompareListDescription'),
                    'value': self.config['unlockCompareList'],
                    'varName': 'unlockCompareList'
                    }
                
                ],
                   
                    'modDisplayName': g_ML.l10n('modDisplayName'),
                    'configName': 'techtree.json',
                    'configVersion': self.config['configVersion'],
                    'enabled': self.config['enabled']}
                
if isImportOK:
    g_MI = MI()
    g_CFG = CFG()
    g_ML = ML()
    g_hook = hook()
    g_TechTree = TechTree()