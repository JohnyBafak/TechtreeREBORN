import xml_compare

""" Check layouts for missing tanks.
    
    Usage from CMD line:
            @param1 = layout folder name (inside DIR folder)
            @param2 = WoT install directory
            @param3 = ignore IGR (IGR rental acc vehicles)
            @param4 = ignore bootcamp (bot, bootcamp, training)
            @param5 = ignore bob&fallout (bob, fallout)
            @param6 = ignore only for epic battle (FL)
            @param7 = ignore steel hunters (SH)
            @param8 = ignore collector's vehicles (SH)
            
    readGame(WOT= "D:/World_of_Tanks_EU", IGR = True, bot=True, bob = True, FL = True, SH = False, collector=False):
    Compare( data, @layout_folder )
"""
data = xml_compare.readGame(SH=False)
xml_compare.Compare( data, '_jbdefault' )

data = xml_compare.readGame(collector=True)
xml_compare.Compare( data, '_KukieJar' )