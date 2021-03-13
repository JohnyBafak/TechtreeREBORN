import tempfile, subprocess, os, shutil, zipfile, glob
import xml.etree.ElementTree as ET
import time, sys
                   
def getVersion(wot):
    """ Check paths.xml for current game version """
    p = 'fail'
    path = wot +'/paths.xml'
    tree = ET.parse(path)
    p = tree.find("Paths")[0].text.split('mods/')[1]
    return p   
    

def main(SOURCE = './xml/jbDefault', WOT = "D:/World_of_Tanks_EU"):
    # runtime
    print "---    XML Export to game    ----"
    print SOURCE, ">>", WOT
    cmd = raw_input("copy XML files with tree-shared.xml?")

    # Copy finish
    destPath = WOT +'/res_mods/' + getVersion(WOT) + '/gui/flash/techtree/' 
    print destPath
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    for file in  os.listdir(SOURCE):
        if file.endswith(".xml"):
            shutil.copy2(os.path.join(SOURCE,file),destPath)
    
    if len(cmd):
            shutil.copy2("tree-shared.xml",destPath)

    print "         Done, Tree-Shared-XML:", True if(len(cmd)) else False
    
if __name__ == "__main__":
    while True:
        main(*sys.argv[1:])
        time.sleep(1)     
     