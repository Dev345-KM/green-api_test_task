import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Green API DevOps Backend")

# 1. Настройка CORS (на всякий случай, если фронтенд будет на другом порту)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники (для теста)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# 2. Определение моделей данных Pydantic (схемы запросов)


class CommonApiCreds(BaseModel):
    idInstance: str
    apiTokenInstance: str


class MessageRequest(CommonApiCreds):
    chatIdMessage: str  # Номер телефона из эскиза
    message: str       # Текст сообщения


class FileRequest(CommonApiCreds):
    chatIdFile: str  # Номер телефона из эскиза
    urlFile: str       # Ссылка на файл
    fileName: str      # Имя файла

# Вспомогательная функция для формирования URL


def get_url(creds: CommonApiCreds, method: str) -> str:
    return f"https://api.green-api.com/waInstance{creds.idInstance}/{method}/{creds.apiTokenInstance}"

# 3. API Эндпоинты


@app.post("/getSettings")
def get_settings(data: CommonApiCreds):
    url = get_url(data, "getSettings")
    try:
        response = requests.get(url, timeout=10)  # Добавили таймаут
        response.raise_for_status()  # Выбросит исключение при 4xx/5xx ошибках
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Green API Error: {str(e)}")


@app.post("/getStateInstance")
def get_state(data: CommonApiCreds):
    url = get_url(data, "getStateInstance")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Green API Error: {str(e)}")


@app.post("/sendMessage")
def send_message(data: MessageRequest):
    url = get_url(data, "sendMessage")
    # Формируем тело запроса для Green API
    payload = {
        "chatId": f"{data.chatIdMessage}@c.us",  # Добавляем суффикс ватсапа
        "message": data.message
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Green API Error: {str(e)}")


@app.post("/sendFileByUrl")
def send_file(data: FileRequest):
    url = get_url(data, "sendFileByUrl")
    payload = {
        "chatId": f"{data.chatIdFile}@c.us",
        "urlFile": data.urlFile,
        "fileName": data.fileName
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Green API Error: {str(e)}")


# 4. Раздача фронтенда (ДОЛЖНО БЫТЬ В КОНЦЕ!)

# Проверяем, существует ли папка static
STATIC_DIR = "static"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Монтируем папку static для доступа к CSS/JS (если они будут в отдельных файлах)
# Будет доступно по URL: http://localhost:8000/static/
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Главная страница. При обращении к '/' отдаем index.html


# Не показываем этот эндпоинт в Swagger UI
@app.get("/", include_in_schema=False)
async def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found in 'static' directory"}
