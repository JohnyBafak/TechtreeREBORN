# ![GitHub Logo](https://github.com/JohnyBafak/TechTreeREBORN/blob/main/build/res/gui/maps/icon/atechtree.png?raw=true) TechtreeREBORN Files

#### ``` ./build/ ``` Folder
Used with my *_build.py* file contains files used for .wotmod  

------

####  ``` ./xml/  ``` Folder
contains current defaul layout files (development version - more up to date, may not work

------

#### ``` ./mods/ ``` Folder
Contains all script files + modsListAPI icon source file

------

#### ``` xml_compare.py ```

Useful for creating current layouts reports, can be used standalone, from cmd line or as a module
When run without any params performs comparison for all layouts
```python
    Usage from CMD line:
      @param1 = layout folder name (inside DIR folder)
      @param2 = WoT install directory
      @param3 = ignore IGR (IGR rental acc vehicles)
      @param4 = ignore bootcamp (bot, bootcamp, training)
      @param5 = ignore bob&fallout (bob, fallout)
      @param6 = ignore only for epic battle (FL)
      @param7 = ignore steel hunters (SH)
      @param8 = ignore collector's vehicles (SH)
````

Functions:

```python 
# when param is set to True vehicle type will be ignored in comparison
readGame(wot="D:/World_of_Tanks_EU", igr=True, bot=True, bob=True, fl=True, sh=False, collector=False):
Compare( data, layout='_jbDefault' )
```
getTanks repport for current game version is required to succesfully run this program.

------

#### ``` xml_export.py ``` 

Exports development layout data into game folder & into release GitHub
Can work both as a module or standalone

Functions:

```python
main(source = './xml/', wot = "D:/World_of_Tanks_EU", name = '_jbDefault', cmd = None):
```
if cmd is not None program will override layout data in release version

------

#### ``` xml_report.py ```

Layout specific xml_compare
- jbDefault: does not ignore Steel Hunters Vehicles
- KukieJar: ignore collector's vehicles


