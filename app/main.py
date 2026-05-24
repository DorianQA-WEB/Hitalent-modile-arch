from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import department


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

app.include_router(department.router)


@app.get("/home")
async def home():
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "API для тестового задания"}
