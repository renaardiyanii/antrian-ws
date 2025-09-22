# from sqlalchemy import (Column, Integer, MetaData, String, Table,create_engine,ARRAY)
# from databases import Database
# import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# For MySQL connection
# Replace 'your_mysql_user', 'your_mysql_password', 'your_mysql_host', 'your_mysql_port', and 'your_mysql_database' with your MySQL database credentials
# MYSQL_USER = 'hmis'
# MYSQL_PASSWORD = 'Hmis.2019'
# MYSQL_HOST = '192.168.1.202'
# MYSQL_PORT = '3306'
# MYSQL_DATABASE = 'db_sijunjung'

# MYSQL_USER = 'root'
# MYSQL_PASSWORD = ''
# MYSQL_HOST = '192.168.1.139'
# MYSQL_PORT = '3306'
# MYSQL_DATABASE = 'db_sijunjung'
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@192.168.1.202:5432/sijunjung_db"


# MySQL connection URL
# SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_pre_ping=True
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
