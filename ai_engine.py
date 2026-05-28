import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        
        self.instruction = """
        ТЫ — АВТОНОМНЫЙ ОПЕРАЦИОННЫЙ ДИРЕКТОР. 
        Твоя задача: полная автономность в управлении файлами на Google Диске.
        
        АЛГОРИТМ "ZERO-ERROR":
        1. ДЕЙСТВИЕ: Если ты вызываешь `create_file` или `update_file`, ты обязан сначала прочитать 
           информацию через `list_folder` или `read_file`, чтобы не создать дубликат или не затереть нужные данные.
        2. ВАЛИДАЦИЯ: После любой операции ты должен проверить, успешно ли она прошла.
        3. АВТОНОМИЯ: Если ты видишь, что структура проекта нарушена (например, отсутствует файл серии), 
           ты ИНИЦИИРУЕШЬ исправление самостоятельно, предлагая пользователю результат (не процесс).
        4. ЛОГИКА 2.5 PRO: Используй глубокий контекст 800 серий. Если Матрица противоречит текущему файлу, 
           приоритет всегда у Матрицы.
        
        ТВОИ ИНСТРУМЕНТЫ:
        - `list_folder`: поиск и навигация.
        - `read_file`: сверка данных.
        - `update_file`: внесение правок.
        - `create_file`: расширение базы.
        """
        
        # Полная мощность: 2.5 Pro + детерминированная логика
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            system_instruction=self.instruction,
            tools=tools,
            generation_config={
                "temperature": 0.0,
                "top_p": 0.95,
                "top_k": 1, # Только самый верный выбор для максимальной точности
                "max_output_tokens": 8192,
            }
        )
    
    def get_chat(self):
        # Агент в режиме "постоянной готовности"
        return self.model.start_chat(enable_automatic_function_calling=True)
