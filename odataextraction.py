import requests
import pandas as pd
import sqlite3
from requests.auth import HTTPBasicAuth
from setup_odata import fetch_data_from_url,apply_modifications

# 0-SalesDocument ,
# 1-SalesOrder ,
# 2-MaterialDocument .
# links = {
#     # 0: "http://192.168.0.200:8020//sap/opu/odata/sap/ZMATERIAL_DATA_ODATA_SRV/ZMATERIAL_DATA_ETSet?$format=json",
#     0:"http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod?$format=json",
#     1: "http://192.168.0.200:8020//sap/opu/odata/sap/ZMKOL_SRV/ZMKOLSet?$format=json",
#     2: "http://192.168.0.200:8020//sap/opu/odata/sap/ZMARDNEW_SRV/ZMARDSETNEWSet?$format=json"
# }
links = {
    0: "http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod",
    1: "http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader",
    2: "http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentItem",
    3:"http://192.168.0.200:8020/sap/opu/odata/sap/API_PHYSICAL_INVENTORY_DOC_SRV/A_PhysInventoryDocItem",
    4:"http://192.168.0.200:8020/sap/opu/odata/sap/API_PHYSICAL_INVENTORY_DOC_SRV/A_PhysInventoryDocHeader"
}

def get_data (baseurl):
    url = baseurl
    auth = HTTPBasicAuth('ananth', 'Gan25e$hA')
    response = requests.get(url, auth=auth)
    return response

def fetch_filtered_data(base_url, value):
    filter_key = "MaterialType" if base_url == links["Material_Details"] else "Plant"
    url = f"{base_url}?&$filter=({filter_key} eq '{value}')&$format=json"
    # print(url)
    auth = HTTPBasicAuth('ankith', 'India321@@')
    response = requests.get(url, auth=auth)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            data = data.get('d', {})
            extracted_data = data.get('results', data.get('value', [data]))
        else:
            extracted_data = data
        
        for record in extracted_data:
            if isinstance(record, dict) and '__metadata' in record:
                del record['__metadata']
        
        return pd.DataFrame(extracted_data)
    else:
        print(f"Error: Request failed with status code {response.status_code}")
        return pd.DataFrame()
    
# def fetch_data_from_url(id):
#     url = links[id]
#     """
#     Fetch data from a URL using Basic Authentication and return it as a Pandas DataFrame.
    
#     Parameters:
#     url (str): The URL to fetch data from.
    
#     Returns:
#     pd.DataFrame: The data retrieved from the URL in a DataFrame format without metadata.
#     """
#     try:
#         # Define the credentials
#         username = 'ananth'
#         password = 'Gan25e$hA'
        
#         # Send GET request with Basic Authentication
#         response = requests.get(url, auth=HTTPBasicAuth(username, password))
        
#         # Raise exception if the request failed
#         response.raise_for_status()
        
#         # Convert JSON response to DataFrame
#         data = response.json()
        
#         # Remove metadata if present
#         if 'd' in data:
#             main_data = data['d'].get('results', [])
#         elif 'value' in data:
#             main_data = data['value']
#         else:
#             main_data = data
        
#         df = pd.DataFrame(main_data)
        
#         # Drop __metadata column if it exists
#         if '__metadata' in df.columns:
#             df.drop(columns=['__metadata'], inplace=True)
#         # print(df)
#         return df
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching data: {e}")
#         return None  # Return an empty DataFrame in case of error

def execute_sql_query(base_url, query, tablename):
    """Fetches data, stores in SQLite temporary memory, and executes SQL query."""
    df = fetch_data_from_url(base_url)
    if df.empty:
        print("No data available to execute query.")
        return pd.DataFrame()
    
    conn = sqlite3.connect(':memory:')
    df.to_sql(tablename, conn, index=False, if_exists='replace')
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result,result.to_dict,result.to_string

if __name__ == "__main__":
    answee = fetch_data_from_url(0)
    # fetch_odata(links['Storage_Location'])
    # yoyo=get_data(links['Storage_Location'])
    # qu = "SELECT * FROM Material Details "
    # data = execute_sql_query(links["Material_Details"], "FERT",qu,"Material Details")
    # print(data)
    # yoyo = fetch_filtered_data("http://192.168.0.200:8020//sap/opu/odata/sap/ZMATERIAL_DATA_ODATA_SRV/ZMATERIAL_DATA_ETSet","FERT")
    # print(yoyo)
    print(answee.info())
    print(answee.head(1))