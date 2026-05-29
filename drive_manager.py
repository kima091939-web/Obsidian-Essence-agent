import io, json
from googleapiclient.discovery import build
from google.oauth2 import service_account

class DriveManager:
    def __init__(self, secrets_dict):
        # Преобразование данных, если пришел словарь или строка
        creds_data = json.loads(secrets_dict) if isinstance(secrets_dict, str) else secrets_dict
        creds = service_account.Credentials.from_service_account_info(
            creds_data,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=creds)

    def list_folder(self, folder_id: str):
        try:
            results = self.service.files().list(q=f"'{folder_id}' in parents and trashed = false").execute()
            return str(results.get('files', []))
        except Exception as e:
            return f"Ошибка доступа к папке: {e}"

    def read_file(self, file_id: str):
        try:
            return self.service.files().get_media(fileId=file_id).execute().decode('utf-8')
        except Exception as e:
            return f"Ошибка чтения файла: {e}"

    def update_file(self, file_id: str, new_content: str):
        try:
            self.service.files().update(fileId=file_id, media_body=io.BytesIO(new_content.encode())).execute()
            return "Файл успешно обновлен."
        except Exception as e:
            return f"Ошибка обновления: {e}"

    def create_file(self, folder_id: str, file_name: str, content: str):
        try:
            meta = {'name': file_name, 'parents': [folder_id]}
            file = self.service.files().create(body=meta, media_body=io.BytesIO(content.encode())).execute()
            return f"Файл {file_name} создан. ID: {file.get('id')}"
        except Exception as e:
            return f"Ошибка создания: {e}"

