from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
load_dotenv()

SQLALCHEMY_DATABASE_URL = "postgresql://antrianonline:4ntr1an0nlin3RSOMHBKT2023!#@192.168.1.139:6742/antrian"
# SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URI')
# SQLALCHEMYSSS = os.getenv('CONSID_ORI')
# print('----------------------')
# print(SQLALCHEMYSSS)
# print('----------------------')
# SQLALCHEMY_DATABASE_URL = os.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,pool_pre_ping=True
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DATABASE_URL = 'postgresql://postgres:postgres@localhost/antrianonline_rsomh'

# engine = create_engine(DATABASE_URL)
# metadata = MetaData()



# database = Database(DATABASE_URL)
