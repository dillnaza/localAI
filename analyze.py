import pandas as pd
import requests
import re
import json
import mimetypes
import fitz  # PyMuPDF для PDF
import docx  # python-docx для DOCX

chat_history = []  # Хранит историю сообщений

def extract_text_from_file(file_name):
    """Определяет тип файла и извлекает текст или данные."""
    mime_type, _ = mimetypes.guess_type(file_name)

    try:
        if mime_type in ["text/csv", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            df = pd.read_csv(file_name) if file_name.endswith(".csv") else pd.read_excel(file_name)
            return f"Вот данные из {file_name}, колонки: {df.columns.tolist()}."

        elif mime_type == "application/json":
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
            return f"Вот JSON-данные из {file_name}: {json.dumps(data, indent=2)}."

        elif mime_type == "text/plain":
            with open(file_name, "r", encoding="utf-8") as f:
                return f"Вот содержимое {file_name}: {f.read()}"

        elif mime_type == "application/pdf":
            doc = fitz.open(file_name)
            text = "\n".join(page.get_text() for page in doc)
            return f"Вот текст из {file_name}: {text[:1000]}..."  # Ограничиваем до 1000 символов

        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file_name)
            text = "\n".join([p.text for p in doc.paragraphs])
            return f"Вот текст из {file_name}: {text[:1000]}..."

    except Exception as e:
        return f"Ошибка обработки файла: {e}"

    return "Формат файла не поддерживается."

def analyze_data(user_input):
    """Анализирует текст или файл и отправляет запрос в AI, сохраняя историю чата."""
    match = re.search(r'(\S+\.(csv|xlsx|json|txt|pdf|docx))', user_input)
    file_name = match.group(1) if match else None

    prompt = user_input
    if file_name:
        prompt = extract_text_from_file(file_name) + f" {user_input}"

    # Добавляем историю чата
    chat_context = "\n".join(chat_history)
    full_prompt = f"{chat_context}\nПользователь: {prompt}\nAI:"

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3",
        "prompt": full_prompt
    }, stream=True)

    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line)
                if "response" in data:
                    full_response += data["response"]
            except json.JSONDecodeError as e:
                print(f"Ошибка обработки JSON: {e}")

    # Добавляем новый диалог в историю
    if full_response.strip():
        chat_history.append(f"Пользователь: {prompt}")
        chat_history.append(f"AI: {full_response.strip()}")

    return full_response.strip() if full_response else "Ошибка: пустой ответ."

# --- Чат с пользователем ---
while True:
    user_request = input("\nВведите вопрос (или 'exit' для выхода): ")
    if user_request.lower() == "exit":
        print("Чат завершен.")
        break
    print("\nОтвет:")
    print(analyze_data(user_request))
