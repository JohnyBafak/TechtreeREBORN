""" 
    Tank List Builder by Johny_Bafak
    ----------
    http://forum.worldoftanks.eu/index.php?/topic/514277-
    Check layouts for missing tanks.
    
    Usage:  @param1 = layout folder name (inside DIR folder)
            @param2 = WoT install directory
            @param3 = ignore IGR (IGR rental acc vehicles)
            @param4 = ignore bootcamp (bot, bootcamp, training)
            @param5 = ignore bob&fallout (bob, fallout)
            @param6 = ignore only for epic battle (FL)
            @param7 = ignore battle royalle (SH)
"""
__version__ = "1.0.0"
NATIONS = [ "czech", "france", "germany", "china", "italy", "japan", "poland", "sweden", "uk", "usa", "ussr" ]
DIR = "../techtreeRelease/xml/"
VER = "fail"

from xml.etree import cElementTree as ET
import sys, os, time

def getVersion(game):
        """ Check paths.xml for current game version """
        global VER
        tree = ET.parse(game + '/paths.xml')
        VER = tree.find("Paths")[0].text.split('mods/')[1]
        
def readGame(wot= "D:/World_of_Tanks_EU", igr = True, bot=True, bob = True, fl = True, sh = True, collector=False, removed=False, china=False):
    getVersion(wot)
    data = {nation: {} for nation in NATIONS}
    fname = '{}/mods/{}_tankList.csv'.format( wot, VER )
    if os.path.isfile( fname ):
        with open(fname) as f:
            delim = f.readline()[6]  
            for line in f:
                X = line.rstrip().split(delim)
                nat = X[0]
                name = X[1]
                
                if "_bot" in name or "_bootcamp" in name or "_training" in name:
                    if bot:     continue
                elif name.endswith("_fallout") or name.endswith("_bob"): 
                    if bob:     continue
                elif name.endswith("_IGR"): 
                    if igr:     continue
                elif name.endswith("_FL"):
                    if fl:      continue
                elif name.endswith("_SH"):    
                    if sh:      continue
                elif X[12] == "True": 
                    if collector:continue
                elif X[9] == "True" and X[7] == "False":
                    if removed: continue
                elif name.endswith("_CN"):
                    if china:   continue
                    
                val = { "lvl": X[5], "cls": X[6] , "gold": X[7] , "hid":X[9], "col":X[12] }
                data[nat][name] = val
    else: raise IOError("[Errno 2] No such file or directory: '{}' Generate vehicle list using jb.getTank first".format(fname))
    return data

class Compare():
    def __init__(self, data, name = "_jbDefault"):
        self.LAYOUT = {}
        self.GAME = data
        for nation in NATIONS:
            self.LAYOUT[nation] = self.readLayout(nation, name)
        
        self.checkDiff(name)
        
        print "Done."
    
    def checkDiff(self, name):
        fname = '{}compare_{}.txt'.format(DIR, name)
        print "writting", fname
        with open (fname, "w") as f:
            f.write("xml_compare_missing for game version {}\n".format(VER))
            for nation in NATIONS:
                inGame = list(self.GAME[nation].keys() )
                XML = list(self.LAYOUT[nation])
                newList = list(set(inGame) - set(XML))
                oldList = list(set(XML) - set(inGame))
                f.write("\n-T----class---gold--hidd-colect-name------------- new {} [{}]\n".format(nation, len(newList) ) ) 
                
                for veh in newList:
                    data = self.GAME[nation][veh]
                    f.write("{:>2} {:>10} {:>5} {:>5} {:>5} {}\n".format(data['lvl'], data['cls'], data['gold'], data['hid'], data['col'], veh ) )
                    #line_new = '{:>12}  {:>12}  {:>12}'.format(word[0], word[1], word[2])
                f.write("xxxxxxxxxxxxxxxxxxxxxxxxxxxxx ------------- removed \n")
                for veh in oldList:
                    f.write(veh+'\n')
        
    def readLayout(self, nation, name):
        xmls =  [ "{}/{}-tree.xml", "{}/{}-premium.xml" ]
        
        nationList = []        
        for path in xmls:
            tree = ET.parse(DIR + path.format(name,nation))
            root = tree.find("nodes")
            for child in root:
                nationList.append( child.tag )
        nationList.sort()
        
        return nationList


if __name__ == "__main__":
    data = readGame(*sys.argv[2:])
    if len(sys.argv) > 1:
        Compare(data, sys.argv[1])
    else: 
        for name in os.listdir(DIR):
            if os.path.isdir(DIR+name):
                Compare(data, name)
            
        
    time.sleep(1)