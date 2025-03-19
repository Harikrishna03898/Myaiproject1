from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime

uri = "mongodb+srv://infosightai:vqrLhpkUPHPfcKZe@cluster0.tzyph.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

def create_project(project_id, project_info, table_dict, access_dict, filters_dict, users_dict):
    """
    Create a new project in MongoDB with the specified data.
    
    Args:
        project_id (str): Unique identifier for the project
        project_info (str): General project information
        table_dict (dict): Dictionary mapping IDs to multiline strings
        access_dict (dict): Dictionary mapping IDs to access levels
        filters_dict (dict): Dictionary mapping access_ids to column filters
        users_dict (dict): Dictionary mapping user_ids to access_ids
    """
    try:
        # Get the database and collection
        db = client['sap_projects']
        projects_collection = db['projects']
        
        # Create project document
        project_data = {
            'project_id': project_id,
            'project_info': project_info,
            'table_dict': table_dict,
            'access_dict': access_dict,
            'filters_dict': filters_dict,
            'users_dict': users_dict,
            'created_at': datetime.datetime.utcnow()
        }
        
        # Insert the document
        result = projects_collection.insert_one(project_data)
        
        if result.inserted_id:
            print(f"Project created successfully with ID: {result.inserted_id}")
            return result.inserted_id
        else:
            print("Failed to create project")
            return None
            
    except Exception as e:
        print(f"Error creating project: {e}")
        return None

def get_project(project_id):
    """
    Retrieve a project from MongoDB by project_id.
    
    Args:
        project_id (str): Unique identifier for the project
    
    Returns:
        dict: Project data if found, None otherwise
    """
    try:
        db = client['sap_projects']
        projects_collection = db['projects']
        
        project = projects_collection.find_one({'project_id': project_id})
        if project:
            # Remove MongoDB's _id field for cleaner output
            project.pop('_id', None)
            return project
        else:
            print(f"No project found with ID: {project_id}")
            return None
    except Exception as e:
        print(f"Error retrieving project: {e}")
        return None

def get_all_projects():
    """
    Retrieve all projects from MongoDB.
    
    Returns:
        list: List of all projects
    """
    try:
        db = client['sap_projects']
        projects_collection = db['projects']
        
        projects = list(projects_collection.find({}, {'_id': 0}))
        return projects
    except Exception as e:
        print(f"Error retrieving projects: {e}")
        return []

def update_project(project_id, update_data):
    """
    Update an existing project in MongoDB.
    
    Args:
        project_id (str): Unique identifier for the project
        update_data (dict): Dictionary containing fields to update
    
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        db = client['sap_projects']
        projects_collection = db['projects']
        
        result = projects_collection.update_one(
            {'project_id': project_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            print(f"Project {project_id} updated successfully")
            return True
        else:
            print(f"No project found with ID: {project_id}")
            return False
    except Exception as e:
        print(f"Error updating project: {e}")
        return False

# Example usage:
if __name__ == "__main__":
    # Create a test project
    m1='''-- Main Material Table
        CREATE TABLE Material_Details (
    MaterialNum TEXT PRIMARY KEY,
    Description TEXT,
    MaterialType TEXT,
    IndustrySector TEXT,
    MaterialGroup TEXT,
    BaseUnit TEXT,
    Plant TEXT,
    MrpType TEXT
);'''
    m2 = '''-- Material Stock Table (linked with Material)
CREATE TABLE Storage_Location (
    Matnr TEXT PRIMARY KEY,
    Plant TEXT,
    Blocked REAL,
    Returns REAL,
    Unrestruse REAL,
    FOREIGN KEY (Matnr) REFERENCES Material(MaterialNum) ON DELETE CASCADE
);'''
    m3 = '''-- Special Material table (linked with Material , where the special materials parts are bought from vendors)
CREATE TABLE Special_Stock (
    MaterialNUM INTEGER PRIMARY KEY,
    Plant TEXT,
    Vendordet INTEGER,
    Stockdelflag BOOLEAN,
    FOREIGN KEY (MaterialNUM) REFERENCES Material(MaterialNum) ON DELETE CASCADE
);'''
    # create_project(
    #     project_id='MM_POC1',
    #     project_info='POC for sap odata connection with sql chatbot with table mara , mard , mkol',
       
    #     table_dict={'0': m1, '1': m2, '2': m3},
    #     access_dict={'1': 'Admin'},
    #     filters_dict={},
    #     users_dict={'i340': '1'}
    # )
    
    # Get the project
    project = get_project('project1')
    if project:
        print("Retrieved project:", project)
    
    # Update the project
    update_data = {
        'project_info': 'Updated test project',
        'table_dict': {'0': 'Updated table data'}
    }
    update_project('projet1', update_data)
    
    # Get all projects
    all_projects = get_all_projects()
    print("All projects:", all_projects)