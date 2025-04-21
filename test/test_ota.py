'''
Firebase Over the Air Updater Test Module:
------------------------------------------
*test ota upater module
 
$ Version: 1.4
@ Author: Yehia Ehab
'''

from src.ota_updater import FirebaseUpdater

updater = FirebaseUpdater(api_key='API_KEY', auth_email='email', auth_pass='pass', database_url='url1', storage_url='url2')
updater.download_latest_version()