import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        # Инструкция требует краткости для голосового синтеза
        self.instruction = """ТЫ — Regalmance XT. Твоя речь должна быть лаконичной, 
        чтобы быть приятной для озвучки. 
        Алгоритм: Аудит -> Анализ -> Исполнение -> Отчет. 
        При упоминании Матрицы сверяйся только с предоставленными файлами."""
        
        self.model = genai.GenerativeModel(
            model_name='gemini-3.5-pro',
            system_instruction=self.instruction,
            tools=tools,
            generation_config={
                "temperature": 0.0, 
                "top_k": 1, 
                "max_output_tokens": 8192
            }
        )
    
    def get_chat(self):
        # Активируем авто-вызов функций для бесшовного управления
        return self.model.start_chat(enable_automatic_function_calling=True)
