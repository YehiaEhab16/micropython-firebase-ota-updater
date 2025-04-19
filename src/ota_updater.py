'''
Firebase Over the Air Updater Module:
-------------------------------------
*used to update microcontroller code over the air from firebase as backend
*initialize an instance of class
*class has one main function:
-download_latest_version:
 get all missing updates and install them on micrcontroller
 
$ Version: 1.2
@ Author: Yehia Ehab
'''

    
# Importing Required Modules
import uos as os
import urequests as requests
from config import Credentials
from gc import collect as gc_collect
from json import dumps as json_dumps
from machine import reset as machine_reset

# Firebase Updater Class
class FirebaseUpdater:
    # Initialize some variables
    def __init__(self):
        self.error = False
        self.downloaded = False
        self.chunks = False
        self.token = None
        self.next_version_number = None
        self.attempts = 0
        self.max_attempts = 2
        self.version_file = 'version.txt'
        
    # Read Version File
    def _read_version_file(self) -> str:
        try:
            with open(self.version_file,'r') as f:
                line = f.readline() # read version
                print("Current version number: ", line)
                return line
        except OSError:
            print("No File")
            return 'v0'
        
    # Write new version to txt file
    def _write_version_file(self,version:str):
        try:
            with open(self.version_file, 'w') as f:
                f.write(str(version)) # write version
        except OSError:
            print("No File")
            
    # Login to firebase
    def _auth_login(self) -> bool:
        try:
            # Firebase URL and login credentials
            url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + Credentials.API_KEY
            data = json_dumps({"email": Credentials.AUTH_EMAIL, "password": Credentials.AUTH_PASSWORD, "returnSecureToken": True })
            headers = {'Content-Type': 'application/json'}
            # Get Response
            response = requests.post(url, data=data, headers=headers)
            if response.status_code == 200:
                self.token = response.json()['idToken']
                return True
            else:
                print(response.json()['error'])
                return False
        except Exception as e:
            print('Login failed due to ', e)
            return False
        
        finally:
            self._clear_memory(response)
        
    # Function to get the latest version number
    def _get_next_version(self,version_number:str) -> dict:
        try:
            # URL of request
            url = f'{Credentials.DATABASE_URL}/.json?auth={self.token}'
            # Get Response
            response = requests.get(url)
            if response.status_code == 200:
                # Compare Versions
                versions = list(response.json().keys())
                versions = [float(version.replace('_', '.')[1:]) for version in versions]
                current_version = float(version_number[1:].replace('_', '.'))
                # Return Next Version Numbers
                for version in sorted(versions):
                    if version > current_version:
                        next_version_key = f'v{str(version).replace(".", "_")}'
                        print("Next Version Number:", next_version_key)
                        self.next_version_number = next_version_key
                        return response.json()[next_version_key]
            print("No new versions")
            return {}
        except Exception as e:
            print('Error getting next version due to ', e)
            return {}
        
        finally:
            self._clear_memory(response)
        
    # Function to download firmware
    def _download_firmware(self,firmware_name:str, server_path:str, firmware_path=''):
        if not self.error:
            try:
                self.attempts += 1
                # Format path
                if firmware_path == '':
                    firmware_path = server_path
                # URL and headers of request
                url = f"{Credentials.STORAGE_URL}%2F{self.next_version_number}%2F{server_path.replace("/", "%2F") + '%2F' if server_path != '.' else ''}{firmware_name}?alt=media"
                headers = {'Authorization': 'Bearer ' + self.token}
                # Get Response
                response = requests.get(url, stream=True, headers=headers)
                if response.status_code == 200:
                    # Save the firmware binary to a file
                    self._write_binary_file(firmware_path, firmware_name, response)
                    print(f"{firmware_name} downloaded successfully to {firmware_path}")
                    
                else:
                    print("Error downloading file due to ", response.json()['error'])
                    self.error = True # Raise flag in case of error

            except Exception as e:
                self._handle_download_error(e, firmware_name, server_path, firmware_path)
            
            finally:
                self._clear_memory(response)
        else:
            print(f"Can't download {firmware_name} due to previous error") 
            
    # Main function -> download and install latest updates
    def download_latest_version(self):
        if self._auth_login():
            while True:
                # Compare current version with latest version
                version_number = self._read_version_file()
                version = self._get_next_version(version_number)
                # In case of new version
                if version != {}:
                    self._download_next_version(version)
                else:
                    if self.downloaded:
                        print('Latest Version installed')
                        print('Resetting ...')
                        machine_reset()
                        
                    else:
                        print('Latest Version already installed')
                        break
                if self.error:
                    print('Error Ocurred while installing version ',self.next_version_number)
                    # In case of successfully installing a version
                    if self.downloaded:
                        print('Resetting ...')
                        machine_reset()
                    # Reset Flags for next attempt
                    else:
                        self.error = False
                        self.attempts = 0
                        break
                
    # Download next version
    def _download_next_version(self,version:dict):
        for loop_counter in range(2):
            # Ensure no errors
            if not self.error:
                for file_path,file_names in version.items():
                    if file_path != 'Size':
                        file_names = file_names.split(';;')
                        for file_name in file_names:
                            if file_name != '':
                                if file_path == '*root*':
                                    file_path = '.'
                                if not loop_counter:    
                                    # Download new files
                                    self._download_firmware(file_name,file_path)
                                
                                else:
                                    # Install new version
                                    self._install_version(file_path, file_name)

        # Write version if all files were downloaded successfully
        if not self.error:
            self._write_version_file(self.next_version_number)
            print('Successfully installed version ',self.next_version_number)
            self.downloaded = True
            
    # Remove old files and rename new files
    def _install_version(self, file_path:str, file_name:str):
        # Remove old files
        try:
            os.remove(file_path + '/' + file_name)
        except:
            print('Old file not removed, could be a new file') # File wasn't installed before
            
        # Rename file to match old one
        try:
            os.rename(file_path + '/new_' + file_name,file_path + '/' + file_name)
        except:
            self.error=True
            print('Possible error during firmware download')

    # Write new file
    def _write_binary_file(self, firmware_path:str, firmware_name:str, response:requests.Response):
        # Make directory if not present
        if firmware_path != '.' and firmware_path.lower() != 'sd':
            if not self._exists_dir(firmware_path):
                os.mkdir(firmware_path)
        # Write file
        with open(firmware_path + '/new_' + firmware_name, 'wb') as f:
            if self.chunks:
                while True:
                    chunk = response.raw.read(1024)
                    if not chunk:
                        break  # Reached end of content
                    f.write(chunk)
                    gc_collect()
            else:
                f.write(response.content) # write file (as bytes)
        
        self.chunks = False
        self.attempts = 0
        
    # Handle Download Errors
    def _handle_download_error(self, exception:Exception, firmware_name:str, server_path:str, firmware_path:str):
        if isinstance(exception, MemoryError) and self.attempts < self.max_attempts:
                print(f'Writing {firmware_name} in chunks due to memory constrains')
                self.chunks = True
                self._download_firmware(firmware_name, server_path, firmware_path)

        elif isinstance(exception, OSError) and exception.args[0] == -29312 and self.attempts < self.max_attempts:
                print(f"Reattempting to download {firmware_name} due to server error")
                self._download_firmware(firmware_name, server_path, firmware_path)

        else:
            print(f"Error downloading {firmware_name} due to ", exception)
            self.error = True # Raise flag in case of error

    # Check if directory aleardy exists
    def _exists_dir(self, path:str) -> bool:
        try:
            os.listdir(path)
            return True
        except:
            return False
            
    # Clear Memory
    def _clear_memory(self, response:requests.Response):
        if 'response' in locals():
            response.close()
        gc_collect()