import os, shutil, time, sys
import xml.etree.ElementTree as ET

def copyXML(source, destPath):
    for file in  os.listdir(source):
        if file.endswith(".xml"):
            shutil.copy2(os.path.join(source,file),destPath)
    
def main(source = './xml/', wot = "D:/World_of_Tanks_EU", name='_jbDefault', cmd = None):
    print "---    XML Export to game    ----\n", source, ">>", wot, "  -  ", name
    if cmd == None: cmd = raw_input("> RELEASE XML files?")

    # Copy files in game
    destPath = wot +'/mods/configs/techtree/xml/dev/'
    print destPath
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    copyXML(source,destPath)
    
    # release XML files 
    if len(cmd):
        destPath = '../techtreeRelease/{}{}'.format(source[2:],name)
        if not os.path.exists(destPath):
            print destPath
            os.makedirs(destPath)
        copyXML(source, destPath)
    print "         Done, release:", (True if(len(cmd)) else False) , "\n"
    
if __name__ == "__main__":
    while True:
        main(*sys.argv[1:])
        time.sleep(1)