from flask import Flask, render_template, request, jsonify
import pandas as pd
from requests.auth import HTTPBasicAuth
import requests
import json
import os
from project_data import odata_links

app = Flask(__name__)

# File to store modifications
MODIFICATIONS_FILE = 'odata_modifications.json'

project_id = "FI001"
links = odata_links(project_id)

# Load existing modifications if file exists
if os.path.exists(MODIFICATIONS_FILE):
    with open(MODIFICATIONS_FILE, 'r') as f:
        modifications_store = json.load(f)
else:
    modifications_store = {}



def apply_modifications(df, url_id):
    print(f"Applying modifications for {url_id}")
    """Apply stored modifications to a dataframe"""
    if str(url_id) not in modifications_store:
        return df
    
    mods = modifications_store[str(url_id)]
    
    # Apply column renames
    if 'renames' in mods:
        df = df.rename(columns=mods['renames'])
    
    # Apply dtype changes
    if 'dtypes' in mods:
        for col, dtype in mods['dtypes'].items():
            if col in df.columns:
                try:
                    if dtype == 'convertedDate':
                        # Convert SAP OData date format to pandas datetime
                        df[col] = df[col].apply(lambda x: pd.to_datetime(int(x[6:-2]), unit='ms').date() if isinstance(x, str) and x.startswith('/Date(') else x)
                    else:
                        df[col] = df[col].astype(dtype)
                except Exception as e:
                    print(f"Could not convert {col} to {dtype}: {str(e)}")
    
    # Drop columns
    if 'drops' in mods:
        df = df.drop(columns=[col for col in mods['drops'] if col in df.columns])
    
    return df

def fetch_data_from_url(id):

    url = f"{links[id]}?$format=json"
    try:
        username = 'ananth'
        password = 'Gan25e$hA'
        
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()
        
        data = response.json()
        
        if 'd' in data:
            main_data = data['d'].get('results', [])
        elif 'value' in data:
            main_data = data['value']
        else:
            main_data = data
        
        df = pd.DataFrame(main_data)
        
        if '__metadata' in df.columns:
            df.drop(columns=['__metadata'], inplace=True)
        
        # Apply any stored modifications
        df = apply_modifications(df, id)
        print('Data fetched successfully from fetch_data_from_url')
            
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    return render_template('setup_odata.html')

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    url_id = int(request.form.get('url_id'))
    df = fetch_data_from_url(url_id)
    
    if not df.empty:
        return jsonify({
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'url_id': url_id
        })
    return jsonify({'error': 'No data found'})

@app.route('/save_modifications', methods=['POST'])
def save_modifications():
    data = request.json
    url_id = str(data.get('url_id'))
    modifications = data.get('modifications')
    
    # Initialize modifications for this URL if it doesn't exist
    if url_id not in modifications_store:
        modifications_store[url_id] = {}
    
    # Update modifications
    modifications_store[url_id].update(modifications)
    
    # Save to file
    with open(MODIFICATIONS_FILE, 'w') as f:
        json.dump(modifications_store, f, indent=2)
    
    return jsonify({'status': 'success', 'message': 'Modifications saved successfully'})

@app.route('/get_urls')
def get_urls():
    return jsonify(links)

if __name__ == '__main__':
    app.run(debug=True, port=5000)