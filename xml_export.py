import tempfile, subprocess, os, shutil, zipfile, glob
import xml.etree.ElementTree as ET
import time

# GLOBAL VARIABLES
WOT = "D:/World_of_Tanks_EU"
SOURCE = './techtree/'

                   
def getVersion():
    """ Check paths.xml for current game version """
    p = 'fail'
    path = WOT +'/paths.xml'
    tree = ET.parse(path)
    p = tree.find("Paths")[0].text.split('mods/')[1]
    return p   
    

def main():
    # runtime
    cmd = raw_input("copy XML files with tree-shared.xml?")

    # Copy finish
    destPath = WOT+'/res_mods/'+getVersion()+'/gui/flash/techtree/'
    for file in  os.listdir("./techtree"):
        if file.endswith(".xml"):
            shutil.copy2("techtree/"+file,destPath)
    
    if len(cmd):
            shutil.copy2("tree-shared.xml",destPath)

    print "         Done, Tree-Shared-XML:", True if(len(cmd)) else False
while True:
    main()      
            
""" 

        OLD 

"""            
            
# AdvancedTechTree Layout Database Builder
def build_LayData(arg):
    global BUILD
    BUILD = tempfile.mkdtemp()
    DATAVER = 'databaseVersion.txt'
    
    with open(DATAVER, 'r') as f:
        number=int(f.read())
    if len(arg) > 2:
        if int(arg[2]) == 9:
            # update version
            number += 1
    
    with zipfile.ZipFile(BUILD+'/AdvancedTechtreeData.zip','w') as zf:
        # write layouts
        for f in glob.iglob('./Layouts/*/*.xml'):
            zf.write(f, './LO/'+f.split('Layouts\\')[1])   
            
        # write nodesLibs
        for f in glob.iglob('./NodeGraphic/*/*.swf'):
            zf.write(f, './Nodes/'+f.split('NodeGraphic\\')[1])   
            
        # write data version
        with open(BUILD + '/' + DATAVER, 'w') as f:
            f.write('%d' % (number))
        zf.write(BUILD + '/' + DATAVER, DATAVER)   
    shutil.copy(BUILD+'/AdvancedTechtreeData.zip', './build/')
    shutil.copy(BUILD + '/' + DATAVER, './')
    print '[     ]   building techtree layout database.... (%s)' % number
        
    try:
        type = int(arg[1])
        if type == 1:
            shutil.copy(BUILD + '/AdvancedTechtreeData.zip', './scripts/BACKUP/database/AdvancedTechtreeData_' + str(number) + '.zip')
            print '[  B  ]   database backup created'
        elif type > 1 and type < len(WOT)+1:
            type -= 1
            folder = WOT[type]+'/mods/resources/'
            if not os.path.isdir(folder):
                os.makedirs(folder)
            shutil.copy(BUILD+'/AdvancedTechtreeData.zip',folder)
            print '[     ]   transfered database in game %s' % WOT[type]
        else: print '[     ]   no transfered database'
    except Exception as E:
        print "[  !  ]   transit error can't copy to %s (%s)" % (WOT[type], E)        
        
    build_finish(arg, number)
    
def build_finish(arg, version):
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    
    if len(arg) > 2:
        if int(arg[2]) == 9:
            mod = int(arg[0]) - 1
            if mod == 3:
                name = './build/AdvancedTechtreeData.zip'
                print '[ >>> ]   > releasing ATT Database %s' % version
                shutil.copy('databaseVersion.txt', './# RELEASE/databaseVersion.txt')
            else:
                name =  './build/' + gINFO[mod]["id"] + '.wotmod'
                print '[ >>> ]   > releasing', gINFO[mod]["id"], version
            shutil.copy(name, './# RELEASE/')
    
            if mod == 0:
                print '[ >>> ]   > building installer files...'
                try:            
                    #subprocess.check_call(['"D:\Program Files\32 Inno Setup 5/compil32.exe" /cc installScript_VerticalTechtree_quick.iss'])
                    #subprocess.check_call(['"D:\Program Files\32 Inno Setup 5/compil32.exe" /cc installScript_VerticalTechtree.iss'])
                    print '[  >  ]     > ATT.zip'
                    install_zip()
                    if INNO is not None:
                        subprocess.check_call('installScript_run.bat "%s"' % INNO)
                    else: 
                        print '[  >  ]     ! no Inno-Setup Compiler'
                except subprocess.CalledProcessError: print ' '
         