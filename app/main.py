from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import time
from starlette.responses import JSONResponse
from app.routers import department
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger
from uuid import uuid4
from celery import Celery, shared_task



@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Запуск приложения: инициализация ресурсов...')
    global db_connection_pool

    try:
        # Инициализация пула соединений с базой данных
        db_connection_pool = {'status': 'connected', 'connection': 'ok'}
        print(f"Пул соединений с базой данных {db_connection_pool} инициализирован.")

        # Здесь можно запустить фоновые задачи, инициализировать кэши и т.д.
        print("Ресурсы успешно инициализированы.")

        yield

    except Exception as e:
        print(f'Ошибка при инициализации ресурсов: {e}')
        raise

    finally:
        print("Завершение работы приложения: закрытие ресурсов...")
    if db_connection_pool:
        db_connection_pool = None
        print("Пул соединений с базой данных закрыт.")



app = FastAPI(
    title='Тестовое задание с модульной архитектурой.',
    version='1.0.0',
    lifespan=lifespan,
    debug=True,
    summary='API для работы с подразделениями и сотрудниками.',
    contact={
        "name": "Владимир",
        'telegram': "@QApanama",
        'email': 'qa.doriangrey@gmail.com'
    },
)

celery = Celery(
    __name__,
    broker='redis://127.0.0.1:6379/0',
    bacekend='redis://127.0.0.1:6379/0',
    broker_connection_retry_on_startup=True
)

@shared_task
def call_background_task(message):
    time.sleep(10)
    print("Background задача запущена")
    print(message)

logger.add("info.log", format='Log: [{extra[log_id]}:{time} - {level} - {message}]', level="INFO", enqueue=True)

app.include_router(department.router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])



@app.get("/home")
async def home(message: str, background_tasks: BackgroundTasks):
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    logger.info("Запрос на корневой маршрут")
    background_tasks.add_task(call_background_task, message)
    return {"message": "API для тестового задания"}

@app.middleware("http")
async def log_middleware(request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401, 403, 404, 409, 422]:
                logger.warning(f'Запрос {request.url.path} ошибку {response.status_code}')
            else:
                logger.info(f'Успешный запрос' + request.url.path)
        except Exception as e:
            logger.error(f'Ошибка при обработке запроса {request.url.path}: {e}')
            response = JSONResponse(content={"success": False}, status_code=500)
        return response