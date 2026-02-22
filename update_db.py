from main import engine, Base

# пересоздание таблицы packages (ОБРАТИ ВНИМАНИЕ — удаляются все данные)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Таблица обновлена!")
