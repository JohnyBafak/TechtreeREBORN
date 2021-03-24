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
            @param8 = ignore collector's vehicles
            @param9 = ignore removed vehicles
            @param10= ignore china specific tanks
            
    readGame(wot="D:/World_of_Tanks_EU", igr=True, bot=True, bob=True, fl=True, sh=False, collector=False, removed=False, china=False):
    Compare( data, @layout_folder )
"""
data = xml_compare.readGame(sh=False)
xml_compare.Compare( data, '_jbdefault' )

data = xml_compare.readGame(collector=True, removed=True, china=True)
xml_compare.Compare( data, '_KukieJar' )