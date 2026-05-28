import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

class DriveManager:
    def __init__(self, creds_info):
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        self.service = build('drive', 'v3', credentials=service_account.Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/drive']))

    def list_folder(self, folder_id):
        """Возвращает список файлов в папке."""
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return str(results.get('files', []))

    def read_file(self, file_id):
        """Читает содержимое файла."""
        request = self.service.files().get_media(fileId=file_id)
        return request.execute().decode('utf-8', errors='ignore')

    def update_file(self, file_id, new_content):
        """Обновляет файл новым текстом."""
        fh = io.BytesIO(new_content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimeType='text/plain', resumable=True)
        self.service.files().update(fileId=file_id, media_body=media).execute()
        return "Файл успешно обновлен на Диске."
