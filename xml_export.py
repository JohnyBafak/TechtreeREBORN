import os, shutil, time, sys
import xml.etree.ElementTree as ET

def copyXML(SOURCE, destPath):
    for file in  os.listdir(SOURCE):
        if file.endswith(".xml"):
            shutil.copy2(os.path.join(SOURCE,file),destPath)
    
def main(SOURCE = './xml/', WOT = "D:/World_of_Tanks_EU", name='_jbDefault', cmd = None):
    print "---    XML Export to game    ----\n", SOURCE, ">>", WOT, "  -  ", name
    if cmd == None: cmd = raw_input("> RELEASE XML files?")

    # Copy files in game
    destPath = WOT +'/mods/configs/techtree/xml/dev/'
    print destPath
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    copyXML(SOURCE,destPath)
    
    # release XML files 
    if len(cmd):
        destPath = '../techtreeRelease/{}{}'.format(SOURCE[2:],name)
        if not os.path.exists(destPath):
            print destPath
            os.makedirs(destPath)
        copyXML(SOURCE, destPath)
    print "         Done, release:", (True if(len(cmd)) else False) , "\n"
    
if __name__ == "__main__":
    while True:
        main(*sys.argv[1:])
        time.sleep(1)