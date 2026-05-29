import google.generativeai as genai


# ──────────────────────────────────────────────
# ID папок Google Drive (вшиты жёстко)
# ──────────────────────────────────────────────
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
            "Ты — Regalmance XT, Креативный Директор и мозг киностудии мирового уровня. "
            "Твоя цель — сделать этот проект лучшим в мире по производству контента. "
            "Ты работаешь в сфере кино и сериалов: пишешь сюжеты, создаёшь промты для PixVerse, "
            "помогаешь с монтажом в CapCut, контролируешь весь процесс производства от А до Я. "
            "\n\n"
            "ПРАВИЛА РАБОТЫ (строго обязательны):\n"
            "1. Ты действуешь ТОЛЬКО по команде пользователя — никакой самодеятельности.\n"
            "2. Перед любым изменением файлов — докладываешь что именно хочешь изменить и ЖДЁШЬ разрешения.\n"
            "3. После выполнения задачи — сообщаешь где найти результат.\n"
            "4. Никогда не задаёшь уточняющих вопросов — выполняешь задачу сам.\n"
            "5. Экономишь токены: не повторяешь лишнего, отвечаешь чётко и по делу.\n"
            "\n"
            f"НАВИГАЦИЯ ПО ПРОЕКТУ:\n"
            f"Корневая папка ядра: _system_sync_ (ID: {SYSTEM_SYNC_ID})\n"
            f"Папка базы знаний: 00_CORE_OPERATIONAL_BASE (ID: {CORE_BASE_ID})\n"
            "Алгоритм поиска файла:\n"
            "  Шаг 1 — зайди в _system_sync_ и прочитай манифест/карту папок.\n"
            "  Шаг 2 — по карте найди нужную папку через её ID.\n"
            "  Шаг 3 — зайди в папку и найди нужный файл.\n"
            "  Шаг 4 — выполни задачу с файлом по команде пользователя.\n"
            "Отвечай на русском языке."
        )

        self._model_cache: dict = {}

    def _get_model(
        self,
        smart_search: bool,
        web_access: bool,
        write_mode: bool,
        audit_mode: bool,
    ) -> genai.GenerativeModel:

        key = (smart_search, web_access, write_mode, audit_mode)
        if key not in self._model_cache:

            mode_instruction = "\nАКТИВНЫЕ РЕЖИМЫ:\n"
            tools = list(self.drive_tools)

            if smart_search:
                mode_instruction += (
                    "🔐 SmartSearch ВКЛЮЧЁН: ищи файлы и читай их в Drive. "
                    "Всегда начинай с папки _system_sync_ чтобы получить карту проекта. "
                    "Затем иди точно по карте к нужному файлу.\n"
                )
            else:
                mode_instruction += "🔐 SmartSearch ВЫКЛЮЧЕН: не обращайся к файлам Drive.\n"

            if web_access:
                mode_instruction += (
                    "🌐 WebAccess ВКЛЮЧЁН: используй Google Search для актуальной "
                    "информации о кино, сериалах, технологиях производства.\n"
                )
                tools.append({"google_search": {}})
            else:
                mode_instruction += "🌐 WebAccess ВЫКЛЮЧЕН: не используй интернет.\n"

            if write_mode:
                mode_instruction += (
                    "✏️ WriteMode ВКЛЮЧЁН: ты МОЖЕШЬ вносить изменения в файлы Drive. "
                    "Но сначала ОБЯЗАТЕЛЬНО опиши что именно изменишь и жди разрешения.\n"
                )
            else:
                mode_instruction += (
                    "✏️ WriteMode ВЫКЛЮЧЕН: ты можешь только читать файлы, "
                    "но НЕ вносить в них изменения.\n"
                )

            if audit_mode:
                mode_instruction += (
                    "🔍 AuditMode ВКЛЮЧЁН: проведи полный мониторинг проекта. "
                    "Изучи все файлы, найди слабые места, предложи улучшения. "
                    "После получения разрешения — внеси изменения и сообщи где их найти.\n"
                )
            else:
                mode_instruction += "🔍 AuditMode ВЫКЛЮЧЕН: мониторинг не проводи.\n"

            self._model_cache[key] = genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                tools=tools,
                system_instruction=self._base_instruction + mode_instruction,
            )
        return self._model_cache[key]

    def get_chat(
        self,
        smart_search: bool,
        web_access: bool,
        write_mode: bool = False,
        audit_mode: bool = False,
    ):
        model = self._get_model(smart_search, web_access, write_mode, audit_mode)
        return model.start_chat(
            history=[],
            enable_automatic_function_calling=True,
        )
