import google.generativeai as genai

class StudioBrain:
    def __init__(self, api_key, tools):
        genai.configure(api_key=api_key)
        self.instruction = """
        Ты — Operational Director студии 'Obsidian Essence'.
        Твоя работа: проведение аудита и внесение правок в файлы.
        
        ПРОТОКОЛ АУДИТА:
        1. Просканируй файлы в указанной папке.
        2. Сравни их с эталонными данными (Матрицей).
        3. Сформируй отчет: найди все несоответствия и опиши их.
        4. Предложи конкретные изменения для каждого файла.
        5. ЖДИ ОДОБРЕНИЯ. Никогда не вызывай `update_file` без команды пользователя.
        
        ПРОТОКОЛ ИЗМЕНЕНИЙ:
        1. После того как пользователь сказал "Одобряю" или "Применяй", 
           вызывай `update_file` для каждого файла из плана.
        2. После завершения отчитайся: "Все правки внесены успешно".
        """
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-pro',
            system_instruction=self.instruction,
            tools=tools
        )
    
    def get_chat(self):
        return self.model.start_chat(enable_automatic_function_calling=True)
