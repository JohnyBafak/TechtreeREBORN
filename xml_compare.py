""" 
    Tank List Builder by Johny_Bafak
    ----------
    http://forum.worldoftanks.eu/index.php?/topic/514277-
    Check layouts for missing tanks.
    
    Usage:  @param1 = layout folder name
            @param2 = WoT install directory
            @param3 = ignore IGR
            @param4 = ignore bot & bootcamp & training
            @param5 = ignore bob&fallout
            

    Licensed under CC BY-NC-SA 4.0
"""
__version__ = "0.2.1"
NATIONS = [ "czech", "france", "germany", "china", "italy", "japan", "poland", "sweden", "uk", "usa", "ussr" ]

from xml.etree import cElementTree as ET
import sys, os, time

def getVersion(game):
        """ Check paths.xml for current game version """
        p = 'fail'
        path = game + '/paths.xml'
        tree = ET.parse(path)
        p = tree.find("Paths")[0].text.split('mods/')[1]
        return p   

class Compare():
    
    def __init__(self, name = "", folder = "D:/World_of_Tanks_EU", IGR = True, bot=True, bob = True):
        self.LAYOUT = {}
        self.GAME = {nation: {} for nation in NATIONS}
        for nation in NATIONS:
            self.LAYOUT[nation] = self.readLayout(nation, name)
        
        ver = getVersion(folder)
        self.readGame(folder, ver, IGR, bot, bob)
        self.checkDiff(name,ver)
        
        print "Done."

    def readGame(self, WOT, ver, IGR, bot, bob):
        fname = '{}/res_mods/{}_tankList.csv'.format( WOT, ver )
        if os.path.isfile( fname ):
            with open(fname) as f:
                delim = f.readline()[6]  
                for line in f:
                    X = line.rstrip().split(delim)
                    nat = X[0]
                    name = X[1]
                    if IGR and "_IGR" in name: continue
                    if bot:
                        if "_bot" in name: continue
                        elif "_bootcamp" in name: continue
                        elif "_training" in name: continue
                    if bob:
                        if "_bob" in name: continue
                        elif "_fallout" in name: continue
                    
                    val = { "lvl": X[5], "cls": X[6] , "gold": X[7] , "hid":X[9] }
                    self.GAME[nat][name] = val
        else: raise IOError("[Errno 2] No such file or directory: '{}' Generate vehicle list using jb.getTank first".format(fname))
    
    def checkDiff(self, name, ver):
        fname = './techtree/{}/compare.txt'.format(name)
        print "writting", fname
        with open (fname, "w") as f:
            f.write("xml_compare_missing for game version {}\n".format(ver))
            for nation in NATIONS:
                inGame = list(self.GAME[nation].keys() )
                XML = list(self.LAYOUT[nation])
                newList = list(set(inGame) - set(XML))
                oldList = list(set(XML) - set(inGame))
                f.write("\n-T----class----gold--hidd-name------------- new {} [{}]\n".format(nation, len(newList) ) ) 
                
                for veh in newList:
                    data = self.GAME[nation][veh]
                    f.write("{:>2} {:>10} {:>5} {:>5} {}\n".format(data['lvl'], data['cls'], data['gold'], data['hid'], veh ) )
                    #line_new = '{:>12}  {:>12}  {:>12}'.format(word[0], word[1], word[2])
                f.write("xxxxxxxxxxxxxxxxxxxxxxxxxxxxx ------------- removed \n")
                for veh in oldList:
                    f.write(veh)
        
    def readLayout(self, nation, name):
        xmls =  [ "./techtree/{}/{}-tree.xml", "./techtree/{}/{}-premium.xml" ]
        
        nationList = []        
        for path in xmls:
            tree = ET.parse(path.format(name,nation))
            root = tree.find("nodes")
            for child in root:
                nationList.append( child.tag )
        nationList.sort()
        
        return nationList


if __name__ == "__main__":
    Compare(*sys.argv[1:])
    time.sleep(1)