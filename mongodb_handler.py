from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import logging
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

class MongoDBHandler:
    def __init__(self):
        self.uri = "mongodb+srv://infosightai:vqrLhpkUPHPfcKZe@cluster0.tzyph.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        
        # Single database with multiple collections
        self.db = self.client['sap_data']
        
        # Initialize collections
        self.projects_collection = self.db['projects_new']
        self.users_collection = self.db['users_new']
        self.access_collection = self.db['access_policy_new']
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def save_project(self, project_data):
        """Save or update project information"""
        try:
            project_data['updated_at'] = datetime.now()
            result = self.projects_collection.update_one(
                {'project_id': project_data['project_id']},
                {'$set': project_data},
                upsert=True
            )
            print(f"info-Project saved: {project_data['project_id']}")
            return result
        except Exception as e:
            print(f"error-Error saving project: {str(e)}")
            raise

    def get_project(self, project_id):
        """Get project by ID"""
        try:
            project = self.projects_collection.find_one({'project_id': project_id}, {'_id': 0})
            if project:
                print(f"info-Project found: {project_id}")
            else:
                print(f"info-Project not found: {project_id}")
            return project
        except Exception as e:
            print(f"error-Error getting project: {str(e)}")
            raise

    def get_all_projects(self):
        """Get all projects"""
        try:
            projects = list(self.projects_collection.find({}, {'_id': 0}))
            print(f"info-Found {len(projects)} projects")
            return projects
        except Exception as e:
            print(f"error-Error getting all projects: {str(e)}")
            raise

    def add_user(self, user_data):
        """Add new user"""
        try:
            user_data['created_at'] = datetime.now()
            result = self.users_collection.insert_one(user_data)
            print(f"info-User added: {user_data.get('user_id')}")
            return result
        except Exception as e:
            print(f"error-Error adding user: {str(e)}")
            raise

    def get_users_by_project(self, project_id):
        """Get all users for a project"""
        return list(self.users_collection.find({'project_id': project_id}, {'_id': 0}))

    def get_all_users(self):
        """Get all users"""
        try:
            users = list(self.users_collection.find({}, {'_id': 0}))
            print(f"info-Found {len(users)} users")
            return users
        except Exception as e:
            print(f"error-Error getting all users: {str(e)}")
            raise

    def save_access_policy(self, policy_data):
        """Save access policy with overwrite if access_id exists"""
        try:
            policy_data['updated_at'] = datetime.now()
            policy_data['access_id'] = str(policy_data['access_id'])  # Ensure string type
            
            # Try to update existing policy first
            result = self.access_collection.update_one(
                {'access_id': policy_data['access_id']},
                {'$set': policy_data},
                upsert=True
            )
            
            action = "updated" if result.matched_count > 0 else "created"
            print(f"info-Access policy {action}: {policy_data['access_id']}")
            return result
        except Exception as e:
            print(f"error-Error saving access policy: {str(e)}")
            raise

    def get_access_policies(self, project_id=None):
        """Get access policies, optionally filtered by project"""
        query = {'project_id': project_id} if project_id else {}
        return list(self.access_collection.find(query, {'_id': 0}))

    def get_all_policies(self):
        """Get all access policies"""
        try:
            policies = list(self.access_collection.find({}, {'_id': 0}))
            print(f"info-Found {len(policies)} access policies")
            return policies
        except Exception as e:
            print(f"error-Error getting access policies: {str(e)}")
            raise

    def get_access_policy(self, access_id):
        """Get access policy by ID"""
        try:
            policy = self.access_collection.find_one({'access_id': access_id}, {'_id': 0})
            if policy:
                print(f"info-Access policy found: {access_id}")
            else:
                print(f"info-Access policy not found: {access_id}")
            return policy
        except Exception as e:
            print(f"error-Error getting access policy: {str(e)}")
            raise

    def update_table_modifications(self, project_id, table_id, modifications):
        """Update table modifications"""
        try:
            result = self.projects_collection.update_one(
                {
                    'project_id': project_id,
                    'tables.table_id': table_id
                },
                {
                    '$set': {
                        'tables.$.modifications': modifications,
                        'updated_at': datetime.now()
                    }
                }
            )
            print(f"info-Table modifications updated: Project {project_id}, Table {table_id}")
            return result
        except Exception as e:
            print(f"error-Error updating table modifications: {str(e)}")
            raise

    def get_project_by_id(self, project_id):
        """Get project by ID (alias for get_project)"""
        return self.get_project(project_id)

    def delete_project(self, project_id):
        """Delete a project by ID"""
        try:
            result = self.projects_collection.delete_one({'project_id': project_id})
            if result.deleted_count > 0:
                print(f"info-Project deleted: {project_id}")
                return True
            else:
                print(f"warning-Project not found for deletion: {project_id}")
                return False
        except Exception as e:
            print(f"error-Error deleting project: {str(e)}")
            raise

    def delete_access_policy(self, access_id):
        """Delete access policy by ID"""
        try:
            result = self.access_collection.delete_one({'access_id': access_id})
            if result.deleted_count > 0:
                print(f"info-Access policy deleted: {access_id}")
                return True
            else:
                print(f"warning-Access policy not found for deletion: {access_id}")
                return False
        except Exception as e:
            print(f"error-Error deleting access policy: {str(e)}")
            raise

    def delete_user(self, user_id):
        """Delete a user by ID"""
        try:
            result = self.users_collection.delete_one({'user_id': user_id})
            if result.deleted_count > 0:
                self.logger.info(f"User deleted: {user_id}")
                return True
            else:
                self.logger.warning(f"User not found for deletion: {user_id}")
                return False
        except Exception as e:
            print(f"error-Error deleting user: {str(e)}")
            raise

    def get_project_complete_info(self, project_id):
        """Get complete project information including related data"""
        try:
            # Get project information
            project_data = self.get_project(project_id)
            if not project_data:
                raise Exception(f"Project {project_id} not found")

            # Initialize result dictionary
            result = {
                'project_id': project_id,
                'project_info': project_data,
                'table_dict': {},
                'access_dict': {},
                'filters_dict': {},
                'users_dict': {}
            }

            # Build table_dict (table_id: schema mapping)
            if 'tables' in project_data:
                result['table_dict'] = {
                    table['table_id']: table['sql_schema']
                    for table in project_data['tables']
                    if 'sql_schema' in table
                }

            # Get all access policies and build access_dict and filters_dict
            access_policies = self.access_collection.find({}, {'_id': 0})
            for policy in access_policies:
                access_id = policy.get('access_id')
                if access_id:
                    # Build access_dict (access_id: [projects])
                    result['access_dict'][access_id] = policy.get('projects', [])
                    
                    # Build filters_dict (table_id: {column_name: [values]})
                    if 'tables' in policy:
                        for table in policy['tables']:
                            table_id = table.get('table_id')
                            if table_id is not None:
                                if table_id not in result['filters_dict']:
                                    result['filters_dict'][table_id] = {}
                                
                                columns = table.get('columns', {})
                                for col_name, value in columns.items():
                                    if value is not None:  # Only include columns with values
                                        if col_name not in result['filters_dict'][table_id]:
                                            result['filters_dict'][table_id][col_name] = []
                                        if value not in result['filters_dict'][table_id][col_name]:
                                            result['filters_dict'][table_id][col_name].append(value)

            # Get all users and build users_dict (user_id: access_id)
            users = self.users_collection.find({}, {'_id': 0})
            result['users_dict'] = {
                user['user_id']: user['access_id']
                for user in users
                if 'user_id' in user and 'access_id' in user
            }

            print(f"info-Complete project info retrieved for project: {project_id}")
            return result

        except Exception as e:
            print(f"error-Error getting complete project info: {str(e)}")
            raise

    def get_projects_list(self):
        """Get list of all projects with basic info"""
        try:
            projects = list(self.projects_collection.find(
                {},
                {
                    '_id': 0,
                    'project_id': 1,
                    'name': 1,
                    'details': 1
                }
            ))
            print(f"info-Found {len(projects)} projects")
            return projects
        except Exception as e:
            print(f"error-Error getting projects list: {str(e)}")
            raise

    def validate_user(self, user_id, password):
        """Validate user credentials"""
        try:
            user = self.users_collection.find_one(
                {
                    'user_id': user_id,
                    'password': password  # In production, use proper password hashing
                },
                {'_id': 0}
            )
            if user:
                print(f"info-User validated: {user_id}")
            else:
                print(f"warning-Invalid login attempt for user: {user_id}")
            return user
        except Exception as e:
            print(f"error-Error validating user: {str(e)}")
            raise

    def get_user_access_details(self, user_id, project_id):
        """Get user's allowed tables and columns based on their access_id and project_id"""
        try:
            # Get user's access_id
            user = self.users_collection.find_one({'user_id': user_id}, {'_id': 0})
            if not user or 'access_id' not in user:
                print(f"error-User not found or no access_id: {user_id}")
                return {}

            access_id = str(user['access_id'])

            # Get access policy for the user's access_id
            policy = self.access_collection.find_one({
                'access_id': access_id
            }, {'_id': 0})

            if not policy or project_id not in policy.get('projects', []):
                print(f"warning-No valid policy found for access_id {access_id} and project {project_id}")
                return {}

            # Build the dictionary {table_id: {'columns': [], 'values': {}}}
            access_dict = {}
            for table in policy.get('tables', []):
                if table.get('project_id') == project_id:
                    table_id = table.get('table_id')
                    if table_id is not None:
                        columns = table.get('columns', {})
                        table_access = {
                            'columns': [],
                            'values': {}
                        }
                        
                        for col, value in columns.items():
                            # Add column to allowed columns list
                            table_access['columns'].append(col)
                            
                            # If value exists and is comma-separated, split into list
                            if value:
                                try:
                                    if isinstance(value, str):
                                        # Split comma-separated values and strip whitespace
                                        values = [v.strip() for v in value.split(',')]
                                        table_access['values'][col] = values
                                    else:
                                        table_access['values'][col] = value
                                except Exception as e:
                                    print(f"warning-Error processing value for column {col}: {str(e)}")
                                    table_access['values'][col] = value

                        if table_access['columns']:  # Only add if there are columns
                            access_dict[table_id] = table_access

            print(f"info-Retrieved access details for user {user_id} in project {project_id}")
            return access_dict

        except Exception as e:
            print(f"error-Error getting user access details: {str(e)}")
            raise

    def get_odata_data(self, project_id, table_id, user_id=None):
        """Fetch and filter OData data based on user access policy"""
        try:
            # Get project info
            project_data = self.get_project(project_id)
            if not project_data:
                print(f"error-Project not found: {project_id}")
                return pd.DataFrame()

            # Find the table info for modifications later
            table = next((t for t in project_data.get('tables', []) 
                         if t.get('table_id') == table_id), None)
            if not table:
                print(f"error-Table {table_id} not found")
                return pd.DataFrame()

            # Get base data without modifications
            df = self._fetch_base_odata_data(project_data, table_id)
            if df.empty:
                print('df is empty')
                return df

            # Apply access policy filters if user_id is provided
            if user_id:
                df = self._apply_access_filters(df, user_id, project_id, table_id)

            if "Warning" in df.columns:
                return df
            
            # Apply table modifications last
            if not df.empty:
                self._apply_table_modifications(df, table)

            return df

        except Exception as e:
            print(f"error-Error in get_odata_data: {str(e)}")
            return pd.DataFrame()

    def _fetch_base_odata_data(self, project_data, table_id):
        """Helper function to fetch base OData data"""
        try:
            # Find the table with matching table_id
            table = next((t for t in project_data.get('tables', []) 
                         if t.get('table_id') == table_id), None)
            
            if not table or not table.get('odata_url'):
                print(f"error-Table {table_id} not found or no OData URL")
                return pd.DataFrame()

            # Fetch data from OData service
            url = f"{table['odata_url']}?$format=json"
            response = requests.get(
                url, 
                auth=HTTPBasicAuth('ananth', 'Gan25e$hA')
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if 'd' in data:
                main_data = data['d'].get('results', [])
            elif 'value' in data:
                main_data = data['value']
            else:
                main_data = data
            
            df = pd.DataFrame(main_data)
            
            # Only remove metadata, no other modifications
            if '__metadata' in df.columns:
                df.drop(columns=['__metadata'], inplace=True)
                
            return df

        except Exception as e:
            print(f"error-Error fetching base OData data: {str(e)}")
            return pd.DataFrame()

    def _apply_access_filters(self, df, user_id, project_id, table_id):
        """Apply access policy filters to the dataframe"""
        try:
            # Get user access details
            access_details = self.get_user_access_details(user_id, project_id)
            if not access_details or table_id not in access_details:
                print(f"warning-No access details found for user {user_id} and table {table_id} ,{access_details}")
                warning_message = f"Warning - Access Restricted for user {user_id} for table {table_id}"
                return pd.DataFrame({"Warning": [warning_message]})  # Return empty if no access

            table_access = access_details[table_id]
            allowed_columns = table_access['columns']
            value_filters = table_access['values']

            # Filter columns
            df = df[allowed_columns]
            print('df after column filter:', df)

            # Apply value filters
            for column, values in value_filters.items():
                if values is not None and column in df.columns:
                    if isinstance(values, list):
                        df = df[df[column].isin(values)]
                    else:
                        df = df[df[column] == values]

            return df

        except Exception as e:
            print(f"error-Error applying access filters: {str(e)}")
            return pd.DataFrame()

    def _apply_table_modifications(self, df, table):
        """Apply stored table modifications"""
        modifications = table.get('modifications', {})
        if modifications:
            # Apply column renames
            if 'renames' in modifications:
                df.rename(columns=modifications['renames'], inplace=True)
            
            # Apply dtype changes
            if 'dtypes' in modifications:
                for col, dtype in modifications['dtypes'].items():
                    if col in df.columns:
                        try:
                            if dtype == 'convertedDate':
                                df[col] = df[col].apply(
                                    lambda x: pd.to_datetime(int(x[6:-2]), unit='ms').date() 
                                    if isinstance(x, str) and x.startswith('/Date(') else x
                                )
                            else:
                                df[col] = df[col].astype(dtype)
                        except Exception as e:
                            print(f"warning-Could not convert {col} to {dtype}: {str(e)}")
            
            # Drop specified columns
            if 'drops' in modifications:
                df.drop(columns=[col for col in modifications['drops'] 
                               if col in df.columns], inplace=True)

if __name__ =="__main__":
    MDB = MongoDBHandler()
    import json
    user_access = MDB.get_user_access_details('i111', 'Business Partner (BP) & Customer Management - 1')
    print("\nAccess Dictionary:")
    for table_id, access in user_access.items():
        print(f"\nTable {table_id}:")
        print(f"Allowed columns: {access['columns']}")
        if access['values']:
            print("\nColumn values:")
            for col, values in access['values'].items():
                print(f"  {col}: {values}")
    # diction = MDB.get_project_complete_info('Business Partner (BP) & Customer Management - 1')
    # for i,j in diction.items():
    #     if i == 'project_info':
    #         continue
    #     if i == 'table_dict':
    #         for k,v in j.items():
    #             print(f'{k} : {v}')
                
    #         continue
    #     print(f'{i} : {j}')