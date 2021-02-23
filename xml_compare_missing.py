""" 
    Tank List Builder by Johny_Bafak
    ----------
    http://forum.worldoftanks.eu/index.php?/topic/514277-
    Check layouts for missing tanks.

    Licensed under CC BY-NC-SA 4.0
    
    v0.2
"""
WOT = "D:/World_of_Tanks_EU"
NATIONS = [ "czech", "france", "germany", "china", "italy", "japan", "poland", "sweden", "uk", "usa", "ussr" ]

from xml.etree import cElementTree as ET
import os, time

def getVersion():
    """ Check paths.xml for current game version """
    p = 'fail'
    path = WOT +'/paths.xml'
    tree = ET.parse(path)
    p = tree.find("Paths")[0].text.split('mods/')[1]
    return p   

class Compare():
    def __init__(self, name = ""):
        self.LAYOUT = {}
        self.GAME = {nation: {} for nation in NATIONS}
        for nation in NATIONS:
            self.LAYOUT[nation] = self.readLayout(nation, name)
        
        ver = getVersion()
        self.readGame(ver)
        self.checkDiff(name,ver)

    def readGame(self, ver):
        fname = '{}/res_mods/{}_tankList.csv'.format( WOT, ver )
        if os.path.isfile( fname ):
            with open(fname) as f:
                delim = f.readline()[6]  
                raw_input(delim)
                for line in f:
                    X = line.rstrip().split(delim)
                    nat = X[0]
                    name = X[1]
                    val = { "lvl": X[5], "cls": X[6] , "gold": X[7] , "hid":X[9] }
                    self.GAME[nat][name] = val
        else: raise IOError("[Errno 2] No such file or directory: '{}' Generate vehicle list using jb.getTank first".format(fname))
    
    def checkDiff(self, name, ver):
        fname = './techtree/{}/compare.txt'.format(name)
        print "writting", fname
        with open (fname, "w") as f:
            f.write("xml_compare_missing for game version {}\n".format(ver))
            for nation in NATIONS:
                f.write("\n-T----class----gold--hidd-name------------- new {}\n".format(nation) ) 
                inGame = list(self.GAME[nation].keys() )
                XML = list(self.LAYOUT[nation])
                newList = list(set(inGame) - set(XML))
                oldList = list(set(XML) - set(inGame))
                
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
    
Compare()
print "Done."
time.sleep(1)