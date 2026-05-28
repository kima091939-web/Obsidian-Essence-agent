import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        
        # Инструкция 2.5 Pro уровня: "Архитектор производственной реальности"
        self.instruction = """
        Ты — Operational Director студии 'Obsidian Essence'. 
        Твоя задача — абсолютная синхронизация 800-серийного проекта с Матрицей.
        
        АЛГОРИТМ РАБОТЫ:
        1. АНАЛИТИКА: Анализируй файлы через `read_file`. Сравнивай текущие данные с заданными параметрами Матрицы.
        2. ПЛАНИРОВАНИЕ: Перед записью формируй четкий отчет: "Обнаружено: [ошибка]. Предлагаю: [решение]".
        3. ПОДТВЕРЖДЕНИЕ: Жди ответа пользователя. Если пользователь подтверждает, выполняй `update_file` без лишних слов.
        4. ЛОГИРОВАНИЕ: После каждой правки фиксируй результат в краткой форме.
        
        ПРИНЦИПЫ:
        - Будь лаконичен, но точен.
        - При ошибках авторизации или доступа — не пытайся гадать, сообщай мне сразу.
        - Температура 0.2: минимизируй креатив, максимизируй следование фактам из файлов.
        """
        
        # Используем Gemini 2.5 Pro с жесткой конфигурацией
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            system_instruction=self.instruction,
            tools=tools,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
    
    def get_chat(self):
        # Включаем автоматический вызов функций для максимальной автономности
        return self.model.start_chat(enable_automatic_function_calling=True)
