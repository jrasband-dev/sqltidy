from .tokenizer.core import SQLScript

def read_sql(file_path: str, dialect: str = "sqlserver") -> SQLScript:
    """
    Reads a SQL file and returns a tokenized SQLScript object.

    Args:
        file_path (str): Path to the SQL file.
        dialect (str): SQL dialect to use for tokenization.

    Returns:
        SQLScript: Tokenized SQL script object.
    """
    if isinstance(file_path, str) and (file_path.endswith('.sql') or '\\' in file_path or '/' in file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()
    else:
        sql = file_path
    return SQLScript.tokenize(sql, dialect)