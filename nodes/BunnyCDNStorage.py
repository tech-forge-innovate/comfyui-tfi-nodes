import base64
import hashlib
import time

import requests


class CDNConnector:

    # constructor
    def __init__(self, api_key, storage_zone, storage_zone_region='de', token_key=''):
        """
            creates an object for using bunnyCDN \n
            api_key=Your Bunny Storage ApiKey/FTP key \n
            storage_zone=Name of your storage zone \n
        """
        self.base_cdn_url = 'https://cdn.techforgeinnovate.com/ai-talking-videos/'

        self.headers = {
            'AccessKey': api_key
        }

        self.token_key = token_key

        if storage_zone_region == 'de' or storage_zone_region == '':
            self.base_url = 'https://storage.bunnycdn.com/' + storage_zone + '/ai-talking-videos/'
        else:
            self.base_url = 'https://' + storage_zone_region + '.storage.bunnycdn.com/' + storage_zone + '/ai-talking-videos/'

    def get_storaged_objects(self, cdn_path):
        """
            returns files and folders stored information stored in CDN (json data)\n
            path=folder path in cdn\n
        """
        request_url = self.base_url + cdn_path

        if cdn_path[-1] != '/':
            request_url = request_url + '/'

        response = requests.request('GET', request_url, headers=self.headers)
        return response.json()

    def get_file(self, cdn_path, download_path=None):
        """
            download file from your cdn storage \n
            cdn_path storage path for the file, (including file name), in cdn, use / as seperator eg, 'images/logo.png' \n
            download_path (default=None, stores in your present working directory) \n
            pass your desired download path with file name, will rewrite already existing files, if do not exists create them.

            Note, directory will not be created
        """
        if cdn_path[-1] == '/':
            cdn_path = cdn_path[:-1]

        filename = cdn_path.split('/')[-1]

        request_url = self.base_url + cdn_path
        response = requests.request("GET", request_url, headers=self.headers)

        if response.status_code == 404:
            raise ValueError('No such file exists')

        if response.status_code != 200:
            raise Exception('Some error, please check all settings once and retry')

        if download_path == None:
            download_path = filename

        with open(download_path, 'wb') as file:
            file.write(response.content)

    def upload_file(self, cdn_path, file_name, file):
        """
            uploads your files to cdn server \n
            cdn_path - directory to save in CDN \n
            filename - name to save with cdn \n
            file_path - locally stored file path,
            if none it will look for file in present working directory
        """
        if type(file) is str:
            with open(file, 'rb') as f:
                file_data = f.read()
        else:
            file_data = file.read()

        # handle empty/None cdn_path safely
        if not cdn_path:
            cdn_path = ''
        elif cdn_path[-1] == '/':
            cdn_path = cdn_path[:-1]

        # build request URL depending on whether cdn_path is empty
        if cdn_path:
            request_url = self.base_url + cdn_path + '/' + file_name
            public_path = self.base_cdn_url + cdn_path + '/' + file_name
        else:
            # upload to root of ai-talking-videos folder
            request_url = self.base_url + file_name
            public_path = self.base_cdn_url + file_name

        response = requests.request("PUT", request_url, data=file_data, headers=self.headers)

        # try to safely parse response json when available
        resp_json = None
        try:
            resp_json = response.json()
        except Exception:
            resp_json = {"status_code": response.status_code, "text": response.text}

        return {
            'filepath': public_path,
            'response': resp_json
        }

    def remove(self, cdn_dir):
        """
            deletes a directory or file from cdn \n
            cdn_dir=complete path including file on CDN \n
            for directory make sure that path ends with /
        """
        request_url = self.base_url + cdn_dir
        response = requests.request('DELETE', request_url, headers=self.headers)
        return response.json()

    def generate_url(self, path: str):
        expires = int(time.time()) + (3600 * 24)

        hash_base = self.token_key + '/ai-talking-videos/' + path + str(expires)

        md5_hash = hashlib.md5(hash_base.encode('utf-8')).digest()
        token = base64.b64encode(md5_hash).decode('utf-8')
        token = token.replace('+', '-').replace('/', '_').replace('=', '')

        url = f"{self.base_cdn_url}{path}?token={token}&expires={expires}"
        return url
