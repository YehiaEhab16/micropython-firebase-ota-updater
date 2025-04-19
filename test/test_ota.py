'''
Firebase Over the Air Updater Test Module:
------------------------------------------
*test ota upater module
 
$ Version: 1.2
@ Author: Yehia Ehab
'''

from src.ota_updater import FirebaseUpdater

FirebaseUpdater().download_latest_version()