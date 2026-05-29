import io, json
from googleapiclient.discovery import build
from google.oauth2 import service_account

class DriveManager:
    def __init__(self, secrets_dict):
        creds = service_account.Credentials.from_service_account_info(
            json.loads(secrets_dict) if isinstance(secrets_dict, str) else secrets_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=creds)

    def list_folder(self, folder_id: str):
        files = self.service.files().list(q=f"'{folder_id}' in parents and trashed = false").execute()
        return str(files.get('files', []))

    def read_file(self, file_id: str):
        return self.service.files().get_media(fileId=file_id).execute().decode('utf-8')

    def update_file(self, file_id: str, new_content: str):
        self.service.files().update(fileId=file_id, media_body=io.BytesIO(new_content.encode())).execute()
        return "Файл обновлен."

    def create_file(self, folder_id: str, file_name: str, content: str):
        file = self.service.files().create(body={'name': file_name, 'parents': [folder_id]}, 
                                          media_body=io.BytesIO(content.encode())).execute()
        return f"Создан ID: {file.get('id')}"
