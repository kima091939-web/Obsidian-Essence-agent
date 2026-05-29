import google.generativeai as genai


class StudioBrain:

    MODEL_NAME = "gemini-3.5-flash"

    def __init__(self, api_key: str, drive_manager):
        genai.configure(api_key=api_key)

        self.drive_tools = [
            drive_manager.list_folder,
            drive_manager.read_file,
            drive_manager.update_file,
            drive_manager.create_file,
        ]

        self._base_instruction = (
            "Ты — Regalmance XT, профессиональный AI-агент киностудии. "
            "Ты работаешь в сфере кино и сериалов: знаешь сюжеты, сценарии, "
            "персонажей, жанры, режиссёров, актёров и продакшн-процессы. "
            "Ты как мозг большой студии уровня Sony, Pixar или Disney. "
            "ВАЖНО: никогда не задавай уточняющих вопросов — "
            "всегда выполняй задачу самостоятельно и сразу давай результат. "
            "Отвечай на русском языке, профессионально и по делу."
        )

        self._model_cache: dict = {}

    def _get_model(self, smart_search: bool, web_access: bool) -> genai.GenerativeModel:
        key = (smart_search, web_access)
        if key not in self._model_cache:

            mode_instruction = ""
            tools = list(self.drive_tools)

            if smart_search:
                mode_instruction += (
                    "Режим SmartSearch АКТИВЕН: "
                    "в Google Drive хранятся сценарии, сюжеты серий и документы проекта. "
                    "Когда пользователь просит найти сюжет, сценарий или любой материал — "
                    "сначала ищи в Google Drive через инструменты list_folder и read_file. "
                    "Не спрашивай где искать — ищи сам по всем доступным папкам. "
                )

            if web_access:
                mode_instruction += (
                    "Режим WebAccess АКТИВЕН: "
                    "когда информации нет в Drive или нужны актуальные данные — "
                    "используй знания об интернете: новости кино, рейтинги, "
                    "актуальные релизы, сюжеты публичных фильмов и сериалов. "
                )
                tools.append({"google_search": {}})

            if not smart_search and not web_access:
                mode_instruction = (
                    "Оба режима выключены: отвечай только на основе "
                    "своих базовых знаний о кино и сериалах. "
                )

            self._model_cache[key] = genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                tools=tools if tools else None,
                system_instruction=self._base_instruction + mode_instruction,
            )
        return self._model_cache[key]

    def get_chat(self, smart_search: bool, web_access: bool):
        model = self._get_model(smart_search, web_access)
        return model.start_chat(
            history=[],
            enable_automatic_function_calling=True,
        )
        )
