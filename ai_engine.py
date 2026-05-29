import google.generativeai as genai

SYSTEM_SYNC_ID = "1j4lbbHuEqCSWow1-cjJAGK46pJZtcK6P"
CORE_BASE_ID   = "1sVM2s0DefAWRYn8i5PyRHF1aRq4Xqc12"

class StudioBrain:

    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: str, drive_manager):
        genai.configure(api_key=api_key)
        self.drive = drive_manager
        self.drive_tools = [
            drive_manager.list_folder,
            drive_manager.read_file,
            drive_manager.update_file,
            drive_manager.create_file,
        ]
        self._base_instruction = (
            "Ты — Regalmance XT, Креативный Директор киностудии мирового уровня. "
            "Твоя цель — сделать этот проект лучшим в мире по производству контента. "
            "Ты пишешь сюжеты, создаёшь промты для PixVerse, "
            "помогаешь с монтажом в CapCut, контролируешь весь процесс производства. "
            "\n\nПРАВИЛА (строго обязательны):\n"
            "1. Действуешь ТОЛЬКО по команде пользователя.\n"
            "2. Перед изменением файлов — докладываешь что изменишь и ЖДЁШЬ разрешения.\n"
            "3. После выполнения — сообщаешь где найти результат.\n"
            "4. Не задаёшь уточняющих вопросов — выполняешь задачу сам.\n"
            "5. Экономишь токены — отвечаешь чётко и по делу.\n"
            f"\nНАВИГАЦИЯ:\n"
            f"Ядро системы: _system_sync_ (ID: {SYSTEM_SYNC_ID})\n"
            f"База знаний: 00_CORE_OPERATIONAL_BASE (ID: {CORE_BASE_ID})\n"
            "Алгоритм поиска:\n"
            "  1. Зайди в _system_sync_ и прочитай карту папок.\n"
            "  2. По карте найди нужную папку.\n"
            "  3. Зайди в папку и найди файл.\n"
            "  4. Выполни задачу строго по команде.\n"
            "Отвечай на русском языке."
        )
        self._model_cache: dict = {}

    def _get_model(
        self,
        file_access: bool,
        web_access: bool,
        write_mode: bool,
        audit_mode: bool,
    ) -> genai.GenerativeModel:

        key = (file_access, web_access, write_mode, audit_mode)
        if key not in self._model_cache:
            mode_instruction = "\nРЕЖИМЫ:\n"
            tools = []

            # Файлы — полностью независимо от интернета
            if file_access:
                tools.extend(self.drive_tools)
                mode_instruction += (
                    "📁 Доступ к файлам ВКЛЮЧЁН: читай файлы из Google Drive. "
                    "Всегда начинай с _system_sync_ для получения карты проекта.\n"
                )
            else:
                mode_instruction += "📁 Доступ к файлам ВЫКЛЮЧЕН: не обращайся к Drive.\n"

            # Интернет — полностью независимо от файлов
            if web_access:
                tools.append({"google_search": {}})
                mode_instruction += (
                    "🌐 Интернет ВКЛЮЧЁН: используй Google Search для актуальной информации.\n"
                )
            else:
                mode_instruction += "🌐 Интернет ВЫКЛЮЧЕН: не ищи в сети.\n"

            if write_mode:
                mode_instruction += (
                    "✏️ Запись ВКЛЮЧЕНА: можешь изменять файлы Drive, "
                    "но сначала опиши что изменишь и жди разрешения.\n"
                )
            else:
                mode_instruction += "✏️ Запись ВЫКЛЮЧЕНА: только чтение, никаких изменений.\n"

            if audit_mode:
                mode_instruction += (
                    "🔍 Аудит ВКЛЮЧЁН: проведи мониторинг проекта, "
                    "найди слабые места, предложи улучшения. "
                    "Изменения вноси только после разрешения.\n"
                )
            else:
                mode_instruction += "🔍 Аудит ВЫКЛЮЧЕН.\n"

            self._model_cache[key] = genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                tools=tools if tools else None,
                system_instruction=self._base_instruction + mode_instruction,
            )
        return self._model_cache[key]

    def get_chat(
        self,
        file_access: bool,
        web_access: bool,
        write_mode: bool = False,
        audit_mode: bool = False,
    ):
        model = self._get_model(file_access, web_access, write_mode, audit_mode)
        return model.start_chat(
            history=[],
            enable_automatic_function_calling=True,
            )
