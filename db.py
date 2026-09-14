import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Do not rely on the directory from which `streamlit run` was started.
# This file owns only the database/mail configuration.
load_dotenv(Path(__file__).with_name(".env"))

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))
