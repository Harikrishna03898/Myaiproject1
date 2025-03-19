import re

def extract_sql_code(input_string):

    # Define the regex pattern to match SQL code starting with SELECT and ending with ;
    pattern = r'SELECT.*?;'
    
    # Use re.DOTALL to make . match newline characters as well
    matches = re.findall(pattern, input_string, re.DOTALL)
    
    # Clean the extracted SQL code by removing newline characters and extra spaces
    clean_sql_code = [re.sub(r'\s+', ' ', match.replace('\n', ' ').strip()) for match in matches]
    
    return clean_sql_code

if __name__ == "__main__":

    schema = '''-- Material Stock Table (linked with Material)
    CREATE TABLE Storage_Location (
        Matnr TEXT PRIMARY KEY,
        Plant TEXT,
        Blocked REAL,
        Returns REAL,
        Unrestruse REAL,
        FOREIGN KEY (Matnr) REFERENCES Material(MaterialNum) ON DELETE CASCADE
    );
    '''
    match = re.search(r"CREATE TABLE (\w+)", schema)
    if match:
        table_name = match.group(1)
        print(f"Table Name: {table_name}")