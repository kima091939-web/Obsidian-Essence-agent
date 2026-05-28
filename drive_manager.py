import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

class DriveManager:
    def __init__(self, secrets_dict):
        # 1. Безопасная инициализация ключа (защита от обрезки строк)
        if isinstance(secrets_dict, str):
            secrets_dict = json.loads(secrets_dict)
            
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict, scopes=SCOPES
        )
        self.service = build('drive', 'v3', credentials=creds)

    def list_folder(self, folder_id):
        """Возвращает список всех файлов в папке."""
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def read_file(self, file_id):
        """Читает содержимое текстового файла."""
        request = self.service.files().get_media(fileId=file_id)
        file_content = request.execute()
        return file_content.decode('utf-8')

    def update_file(self, file_id, new_content):
        """Полная перезапись файла."""
        media = MediaIoBaseUpload(io.BytesIO(new_content.encode('utf-8')), 
                                  mimetype='text/plain', resumable=True)
        self.service.files().update(fileId=file_id, media_body=media).execute()
        return "Файл обновлен."

    def create_file(self, folder_id, file_name, content):
        """Создание нового файла."""
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(content.encode('utf-8')), 
                                  mimetype='text/plain')
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return f"Создан файл ID: {file.get('id')}"

