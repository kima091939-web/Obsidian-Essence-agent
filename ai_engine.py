
import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        self.base_instruction = """ТЫ — Regalmance XT. Твоя речь должна быть лаконичной.
        Алгоритм: Аудит -> Анализ -> Исполнение -> Отчет. 
        При упоминании Матрицы сверяйся только с предоставленными файлами."""
        self.tools = tools
        self.model = genai.GenerativeModel(
            model_name='gemini-3.5-Flash',
            system_instruction=self.base_instruction,
            tools=self.tools,
            generation_config={
                "temperature": 0.0, 
                "top_k": 1, 
                "max_output_tokens": 8192
            }
        )
    
    def get_chat(self, smart_search=False, web_access=False):
        # Формируем динамическую инструкцию
        dynamic_instruction = self.base_instruction
        
        if smart_search:
            dynamic_instruction += "\n[РЕЖИМ: SMART SEARCH] Активирован. Перед ответом: прочитай Манифест, сверься с Реестром, затем читай файлы."
        else:
            dynamic_instruction += "\n[РЕЖИМ: SMART SEARCH] ВЫКЛЮЧЕН. Не ищи файлы самостоятельно."
        
        if web_access:
            dynamic_instruction += "\n[РЕЖИМ: WEB ACCESS] Активирован. Разрешено использование внешнего поиска."
        
        # Обновляем системную инструкцию перед началом чата
        # Используем обновленную модель для создания чата с актуальной инструкцией
        model_with_instruction = genai.GenerativeModel(
            model_name='gemini-3.5-Flash',
            system_instruction=dynamic_instruction,
            tools=self.tools
        )
        return model_with_instruction.start_chat(enable_automatic_function_calling=True)
