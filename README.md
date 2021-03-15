# TechtreeREBORN Files

### ``` ./build/ ``` Folder
Used with my *_build.py* file contains files used for .wotmod  

###  ``` ./xml/  ``` Folder
contains current defaul layout files (development version - more up to date, may not work

### ``` ./mods/ ``` Folder
Contains all script files + modsListAPI icon source file

### ``` xml_compare.py ```

Useful for creating current layouts reports, can be used standalone, from cmd line or as a module
When run without any params performs comparison for all layouts

    Usage from CMD line:
      @param1 = layout folder name (inside DIR folder)
      @param2 = WoT install directory
      @param3 = ignore IGR (IGR rental acc vehicles)
      @param4 = ignore bootcamp (bot, bootcamp, training)
      @param5 = ignore bob&fallout (bob, fallout)
      @param6 = ignore only for epic battle (FL)
      @param7 = ignore steel hunters (SH)
      @param8 = ignore collector's vehicles (SH)
            
Functions:
    ```python 
    # when param is set to True vehicle type will be ignored in comparison
    readGame(WOT= "D:/World_of_Tanks_EU", IGR = True, bot=True, bob = True, FL = True, SH = False, collector=False):
    Compare( data, layout='_jbDefault' )
    ```
  
### ``` xml_export.py ``` 

Exports development layout data into game folder & into release GitHub
Can work both as a module or standalone

Functions:

    main(SOURCE = './xml/', WOT = "D:/World_of_Tanks_EU", name='_jbDefault', cmd = None):


### ``` xml_report.py ```

Layout specific xml_compare
- jbDefaul: does not ignore Steel Hunters Vehicles
- KukieJar: ignore collector's vehicles


