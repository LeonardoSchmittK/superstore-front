import sqlalchemy
import pandas as pd
from config import DB_CONFIG

def get_engine():
    url = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return sqlalchemy.create_engine(url)

def query(sql):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)
