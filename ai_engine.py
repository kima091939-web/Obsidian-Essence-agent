import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, drive_manager):
        genai.configure(api_key=api_key)
        self.drive = drive_manager
        self.tools = [self.drive.list_folder, self.drive.read_file, self.drive.update_file, self.drive.create_file]
        self.base_instruction = "ТЫ — Regalmance XT. Действуй строго по алгоритму: Аудит -> Анализ -> Исполнение -> Отчет."

    def get_chat(self, smart_search: bool, web_access: bool):
        # Динамическое формирование инструкций
        instruction = self.base_instruction
        if smart_search: 
            instruction += "\n[РЕЖИМ: SMART SEARCH] Активирован. Обязательно сверяйся с Реестром и изучай файлы на диске."
        else:
            instruction += "\n[РЕЖИМ: SMART SEARCH] Выключен. Не производи самостоятельный поиск по файлам."
            
        if web_access: 
            instruction += "\n[РЕЖИМ: WEB ACCESS] Активирован. Разрешено использование внешнего поиска."
        
        # Создание модели с обновленными инструкциями
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=instruction,
            tools=self.tools
        )
        return model.start_chat(enable_automatic_function_calling=True)

