import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, drive_manager):
        genai.configure(api_key=api_key)
        self.tools = [
            drive_manager.list_folder, 
            drive_manager.read_file, 
            drive_manager.update_file, 
            drive_manager.create_file
        ]
        self.base_instruction = "ТЫ — Regalmance XT (версия 3.5). Действуй строго: Аудит -> Анализ -> Исполнение."
        # Установлена модель gemini-3.5-flash
        self.model = genai.GenerativeModel('gemini-3.5-flash', tools=self.tools)

    def get_chat(self, smart_search, web_access):
        instruction = self.base_instruction
        if smart_search: instruction += "\n[РЕЖИМ: SMART SEARCH] АКТИВИРОВАН."
        if web_access: instruction += "\n[РЕЖИМ: WEB ACCESS] АКТИВИРОВАН."
        
        return self.model.start_chat(
            history=[], 
            enable_automatic_function_calling=True
        )
