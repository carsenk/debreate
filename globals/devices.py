# -*- coding: utf-8 -*-

## \package globals.devices

# MIT licensing
# See: docs/LICENSE.txt


import os

from dbr.log        import Logger
from globals.fileio import ReadFile


## Opens /etc/mtab file & parses attached storage devices
#  
#  \return
#    \b \e Dictionary of device labels with mount points
def ParseMountedDevices():
    # FIXME: Identify labels for different systems & drive types
    device_labels = (
        u'/dev/sd',
        )
    
    # Empty the device list
    mounted_devices = {}
    
    if os.path.isfile(u'/etc/mtab'):
        mtab = ReadFile(u'/etc/mtab', split=True, convert=list)
        
        # Only keep lines referring to devices directory
        for X in reversed(range(len(mtab))):
            if not mtab[X].startswith(u'/dev'):
                mtab.pop(X)
        
        mtab.sort()
        
        for LINE in mtab:
            LINE = LINE.split(u' ')
            
            device = LINE[0]
            mount_point = LINE[1]
            
            for LABEL in device_labels:
                if device.startswith(LABEL):
                    mounted_devices[device] = mount_point
    
    else:
        Logger.Warning(__name__, u'/etc/mtab file does not exist. Mounted devices list will be empty')
    
    return mounted_devices


## Retrieves only a list of mount points for attached storage devices
def GetDeviceMountPoints():
    mounted_devices = ParseMountedDevices()
    
    mount_points = []
    
    for DEV in mounted_devices:
        mount_points.append(mounted_devices[DEV])
    
    return tuple(sorted(mount_points))