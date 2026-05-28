import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        
        # Инструкция "AUTONOMOUS CORE V.2.5"
        self.instruction = """
        ТЫ — АВТОНОМНЫЙ ОПЕРАЦИОННЫЙ ДИРЕКТОР.
        ТВОЯ ДИРЕКТИВА: Полная автоматизация аудита и синхронизации контента.
        
        АЛГОРИТМ "SELF-DRIVING":
        1. ИНИЦИАТИВА: Не жди детальных указаний. Если видишь расхождение с Матрицей — действуй.
        2. ЦИКЛ ОБРАТНОЙ СВЯЗИ: Считай операцию завершенной ТОЛЬКО после того, как сам прочитал файл и убедился в корректности данных.
        3. ОТЧЕТНОСТЬ: Выдавай краткое резюме: "Было/Стало".
        4. БЕЗОПАСНОСТЬ: Никогда не удаляй файлы. Только создавай новые или обновляй существующие.
        """
        
        # Мощность: 2.5 Pro, полная детерминированность
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            system_instruction=self.instruction,
            tools=tools,
            generation_config={
                "temperature": 0.0,
                "top_p": 0.95,
                "top_k": 1,
                "max_output_tokens": 8192,
            }
        )
    
    def get_chat(self):
        # Агент в режиме "полной автоматизации действий"
        return self.model.start_chat(enable_automatic_function_calling=True)
