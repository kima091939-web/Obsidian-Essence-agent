import io, json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

class DriveManager:
    def __init__(self, secrets_dict):
        if isinstance(secrets_dict, str): secrets_dict = json.loads(secrets_dict)
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict, 
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=creds)
        # Сохраняем ссылку на объект для связи с Brain (если потребуется)
        self.brain = None 

    def list_folder(self, folder_id):
        """Интеллектуальный аудит папки."""
        try:
            files = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false", 
                fields="files(id, name)"
            ).execute()
            return files.get('files', [])
        except Exception as e:
            return f"Ошибка доступа к папке: {str(e)}"

    def read_file(self, file_id):
        """Чтение данных — только по прямому запросу."""
        try:
            return self.service.files().get_media(fileId=file_id).execute().decode('utf-8')
        except Exception as e:
            return f"Ошибка чтения: {str(e)}"

    def update_file(self, file_id, new_content):
        """Синхронизация с Матрицей."""
        media = MediaIoBaseUpload(io.BytesIO(new_content.encode('utf-8')), mimetype='text/plain', resumable=True)
        self.service.files().update(fileId=file_id, media_body=media).execute()
        return "Файл успешно синхронизирован с Матрицей."

    def create_file(self, folder_id, file_name, content):
        """Создание новой структуры."""
        meta = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(content.encode('utf-8')), mimetype='text/plain')
        file = self.service.files().create(body=meta, media_body=media, fields='id').execute()
        return f"Создан объект: {file_name} (ID: {file.get('id')})"


