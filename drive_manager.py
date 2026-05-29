import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account


class DriveManager:
    """
    Менеджер Google Drive.
    Поддерживает: чтение, создание, обновление файлов и листинг папок.
    """

    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, secrets_dict: dict | str):
        """
        secrets_dict — словарь или JSON-строка с ключами сервисного аккаунта.
        """
        if isinstance(secrets_dict, str):
            secrets_dict = json.loads(secrets_dict)

        creds = service_account.Credentials.from_service_account_info(
            secrets_dict,
            scopes=self.SCOPES,
        )
        self.service = build("drive", "v3", credentials=creds)

    # ──────────────────────────────────────────────
    # Инструменты (вызываются Gemini как functions)
    # ──────────────────────────────────────────────

    def list_folder(self, folder_id: str) -> str:
        """
        Возвращает список файлов в папке Google Drive.

        Args:
            folder_id: ID папки Google Drive.

        Returns:
            Строка со списком файлов (name, id, mimeType).
        """
        try:
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="files(id, name, mimeType, modifiedTime)",
                )
                .execute()
            )
            files = results.get("files", [])
            if not files:
                return "Папка пуста или не найдена."
            return "\n".join(
                f"📄 {f['name']} | ID: {f['id']} | Тип: {f['mimeType']}"
                for f in files
            )
        except Exception as e:
            return f"Ошибка list_folder: {e}"

    def read_file(self, file_id: str) -> str:
        """
        Читает содержимое текстового файла из Google Drive.

        Args:
            file_id: ID файла Google Drive.

        Returns:
            Текстовое содержимое файла.
        """
        try:
            content = (
                self.service.files()
                .get_media(fileId=file_id)
                .execute()
            )
            return content.decode("utf-8")
        except Exception as e:
            return f"Ошибка read_file: {e}"

    def update_file(self, file_id: str, new_content: str) -> str:
        """
        Обновляет содержимое существующего файла в Google Drive.

        Args:
            file_id: ID файла для обновления.
            new_content: Новое текстовое содержимое.

        Returns:
            Сообщение об успехе или ошибке.
        """
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(new_content.encode("utf-8")),
                mimetype="text/plain",
                resumable=False,
            )
            self.service.files().update(
                fileId=file_id,
                media_body=media,
            ).execute()
            return f"✅ Файл {file_id} успешно обновлён."
        except Exception as e:
            return f"Ошибка update_file: {e}"

    def create_file(self, folder_id: str, file_name: str, content: str) -> str:
        """
        Создаёт новый текстовый файл в указанной папке Google Drive.

        Args:
            folder_id: ID папки, где создать файл.
            file_name: Имя нового файла (например, "report.txt").
            content: Текстовое содержимое файла.

        Returns:
            ID созданного файла или сообщение об ошибке.
        """
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode("utf-8")),
                mimetype="text/plain",
                resumable=False,
            )
            file_meta = {
                "name": file_name,
                "parents": [folder_id],
            }
            created = self.service.files().create(
                body=file_meta,
                media_body=media,
                fields="id, name",
            ).execute()
            return f"✅ Файл '{created['name']}' создан. ID: {created['id']}"
        except Exception as e:
            return f"Ошибка create_file: {e}"
