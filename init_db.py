from database import engine, Base
import models

Base.metadata.create_all(bind=engine)
print(" База данных и таблицы успешно созданы.")
