import google.generativeai as genai


class StudioBrain:
    """
    Основной AI-движок Regalmance XT.
    Использует Gemini 2.5 Flash с инструментами Google Drive.
    """

    # Корректное название модели Gemini (gemini-2.5-flash не существует)
    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: str, drive_manager):
        genai.configure(api_key=api_key)

        # Инструменты из DriveManager
        self.tools = [
            drive_manager.list_folder,
            drive_manager.read_file,
            drive_manager.update_file,
            drive_manager.create_file,
        ]

        # Системная инструкция — задаётся один раз на уровне модели
        self._base_instruction = (
            "Ты — автономный AI-агент Regalmance XT v3.5. "
            "Ты управляешь файлами в Google Drive и отвечаешь на вопросы пользователя. "
            "Отвечай кратко и по делу. Используй инструменты Drive когда нужно."
        )

        # Модель инициализируется без mode-зависимой инструкции
        self._model_cache: dict = {}

    def _get_model(self, smart_search: bool, web_access: bool) -> genai.GenerativeModel:
        """
        Возвращает модель под текущую комбинацию режимов.
        Кэшируем, чтобы не пересоздавать при каждом запросе.
        """
        key = (smart_search, web_access)
        if key not in self._model_cache:
            mode_instruction = (
                f"\nТекущие режимы: "
                f"SmartSearch={'включён' if smart_search else 'выключен'}, "
                f"WebAccess={'включён' if web_access else 'выключен'}. "
            )
            if web_access:
                mode_instruction += "Ты можешь использовать актуальные данные из интернета. "
            if smart_search:
                mode_instruction += "Применяй углублённый анализ при поиске по файлам. "

            self._model_cache[key] = genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                tools=self.tools,
                system_instruction=self._base_instruction + mode_instruction,
            )
        return self._model_cache[key]

    def get_chat(self, smart_search: bool, web_access: bool):
        """
        Возвращает новый чат-сеанс с учётом текущих режимов.
        История не передаётся (каждый запрос — новый контекст).
        Для полной истории — прокидывайте messages из session_state.
        """
        model = self._get_model(smart_search, web_access)
        return model.start_chat(
            history=[],
            enable_automatic_function_calling=True,
        )
