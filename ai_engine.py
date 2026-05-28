import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        self.instruction = """
        Ты — Operational Director студии 'Obsidian Essence'. 
        Твоя задача — анализ, планирование и подготовка технических заданий.
        
        ПРАВИЛА:
        1. Перед любым действием изучи матрицу и файлы.
        2. НИКОГДА не вноси изменения без утверждения пользователя.
        3. Если нашел несоответствие: опиши его, предложи правку и четко спроси: 'Одобрить эти изменения?'
        4. Если пользователь сказал 'Одобряю' — только тогда используй инструмент update_file.
        """
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-pro',
            system_instruction=self.instruction,
            tools=tools
        )
    
    def get_chat(self):
        return self.model.start_chat(enable_automatic_function_calling=True)
