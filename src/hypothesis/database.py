from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()

HOST = os.getenv("pg_host")
PORT = os.getenv("pg_port")
DATABASE = os.getenv("pg_database")
USER = os.getenv("pg_username")
PASSWORD = os.getenv("pg_password")


connect = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

def engine() -> Engine:
    '''Returns SQL Alchemy engine object\n
    Used with python context manager
    '''
    alchemy_engine = create_engine(connect)
    print("DB connected")
    return alchemy_engine


ENGINE = engine()


def read(script: str, subdir: str = '') -> str:
    '''
    func return's .sql script from src/database/scripts folder\n
    for script you must enter "file_name.sql"\n
    for subdir you must enter the dir between ../scripts and file_name.sql. This made for dir specification 
    '''

    DIR = f'{os.getcwd()}/src/hypothesis/scripts'
    
    with open(f'{DIR}{subdir}/{script}', 'r') as f:
        return f.read()

# print(f'{os.getcwd()}/src')