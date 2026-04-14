##Aqui se crea la base de datos con la que trabajara el sistema 
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
##sqlalchemy se utiliza para crear la conexion con la base de datos 
from app.config import settings

##Aqui se crea crea la base de datos, a la cual despues se le agregaran modelos para agregarle informacion
class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
