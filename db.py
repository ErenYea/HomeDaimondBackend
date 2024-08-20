import pyodbc

def get_db_connection():
    server = 'dhpdevazsql01.database.windows.net'
    database = 'dhpdevdb01'
    username = 'dhpdevwebappdb01'
    password = 'Z.M!EpvtWa!i233zq!pzyNP4Hkn4*CEKeeCwkcv4C'
    driver = '{ODBC Driver 17 for SQL Server}'
    
    connection_string = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
    return pyodbc.connect(connection_string)
