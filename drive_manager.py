import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account


class DriveManager:
    """
    Менеджер Google Drive + Google Docs.
    Поддерживает: чтение текстовых файлов, Google Docs, создание, обновление и листинг папок.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents.readonly",
    ]

    # MIME-типы Google Docs Editor файлов
    GOOGLE_DOCS_MIME    = "application/vnd.google-apps.document"
    GOOGLE_SHEETS_MIME  = "application/vnd.google-apps.spreadsheet"
    GOOGLE_SLIDES_MIME  = "application/vnd.google-apps.presentation"
    GOOGLE_FOLDER_MIME  = "application/vnd.google-apps.folder"

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
        self.docs_service = build("docs", "v1", credentials=creds)

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
        Читает содержимое файла из Google Drive.
        Автоматически определяет тип файла:
        - Google Docs → экспортирует как plain text
        - Google Sheets → экспортирует как CSV
        - Google Slides → экспортирует как plain text
        - Обычные файлы → читает напрямую

        Args:
            file_id: ID файла Google Drive.

        Returns:
            Текстовое содержимое файла.
        """
        try:
            # Определяем тип файла
            meta = self.service.files().get(
                fileId=file_id,
                fields="mimeType, name"
            ).execute()
            mime = meta.get("mimeType", "")
            name = meta.get("name", file_id)

            # Google Docs → экспорт в plain text
            if mime == self.GOOGLE_DOCS_MIME:
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/plain"
                ).execute()
                if isinstance(content, bytes):
                    return content.decode("utf-8")
                return str(content)

            # Google Sheets → экспорт в CSV
            elif mime == self.GOOGLE_SHEETS_MIME:
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/csv"
                ).execute()
                if isinstance(content, bytes):
                    return content.decode("utf-8")
                return str(content)

            # Google Slides → экспорт в plain text
            elif mime == self.GOOGLE_SLIDES_MIME:
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/plain"
                ).execute()
                if isinstance(content, bytes):
                    return content.decode("utf-8")
                return str(content)

            # Папка — нельзя читать как файл
            elif mime == self.GOOGLE_FOLDER_MIME:
                return f"⚠️ '{name}' — это папка. Используй list_folder для просмотра содержимого."

            # Обычный текстовый файл
            else:
                content = (
                    self.service.files()
                    .get_media(fileId=file_id)
                    .execute()
                )
                if isinstance(content, bytes):
                    return content.decode("utf-8")
                return str(content)

        except Exception as e:
            return f"Ошибка read_file: {e}"

    def update_file(self, file_id: str, new_content: str) -> str:
        """
        Обновляет содержимое существующего файла в Google Drive.
        Работает только для plain text файлов.
        Для Google Docs используй create_file для создания новой версии.

        Args:
            file_id: ID файла для обновления.
            new_content: Новое текстовое содержимое.

        Returns:
            Сообщение об успехе или ошибке.
        """
        try:
            # Проверяем тип файла
            meta = self.service.files().get(
                fileId=file_id,
                fields="mimeType, name"
            ).execute()
            mime = meta.get("mimeType", "")

            if mime in (self.GOOGLE_DOCS_MIME, self.GOOGLE_SHEETS_MIME, self.GOOGLE_SLIDES_MIME):
                return (
                    f"⚠️ Файл является Google Docs Editor файлом ({mime}). "
                    "Прямое обновление недоступно. "
                    "Используй create_file для создания нового текстового файла."
                )

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
