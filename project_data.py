from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://infosightai:vqrLhpkUPHPfcKZe@cluster0.tzyph.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

def odata_links(project_id):
    project_id_links ={
        'Business Partner (BP) & Customer Management -1':{0:"http://192.168.0.200:8020//sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner",
             1:"http://192.168.0.200:8020//sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Customer",
             2:"http://192.168.0.200:8020//sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Supplier"},
        'FI001':{
            0:"http://192.168.0.200:8020//sap/opu/odata/sap/API_GLACCOUNTINCHARTOFACCOUNTS_SRV/A_GLAccountInChartOfAccounts",
            1:"http://192.168.0.200:8020//sap/opu/odata/sap/API_GLACCOUNTINCHARTOFACCOUNTS_SRV/A_GLAccountText"

        },
        'SD001':{
            0:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder",
            1:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderHeaderPartner",
            2:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderItem",
            3:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderItemPartner",
            4:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderItemPrElement",
            5:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderItemText",
            6:"http://192.168.0.200:8020//sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderScheduleLine"

        },
        '111':{
            0: "http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod",
            1: "http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader",
            2: "http://192.168.0.200:8020/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentItem",
            3:"http://192.168.0.200:8020/sap/opu/odata/sap/API_PHYSICAL_INVENTORY_DOC_SRV/A_PhysInventoryDocItem",
            4:"http://192.168.0.200:8020/sap/opu/odata/sap/API_PHYSICAL_INVENTORY_DOC_SRV/A_PhysInventoryDocHeader"
        }

    }
    
    return project_id_links.get(str(project_id), {})

def get_project_formatted(project_id):
    """
    Retrieve a project from MongoDB and convert string keys to integers where appropriate.
    
    Args:
        project_id (str): Unique identifier for the project
    
    Returns:
        dict: Project data with integer keys where appropriate, None if not found
    """
    try:
        db = client['sap_projects']
        projects_collection = db['projects']
        
        project = projects_collection.find_one({'project_id': project_id})
        if not project:
            print(f"No project found with ID: {project_id}")
            return None
            
        # Remove MongoDB's _id field
        project.pop('_id', None)
        
        # Convert string keys to integers where appropriate
        if 'table_dict' in project:
            project['table_dict'] = {int(k): v for k, v in project['table_dict'].items()}
            
        if 'access_dict' in project:
            project['access_dict'] = {int(k): v for k, v in project['access_dict'].items()}
            
        if 'filters_dict' in project:
            project['filters_dict'] = {
                int(k): v for k, v in project['filters_dict'].items()
            }
            
        if 'users_dict' in project:
            project['users_dict'] = {k: int(v) for k, v in project['users_dict'].items()}
            
        return project
        
    except Exception as e:
        print(f"Error retrieving project: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    project = get_project_formatted('111')
    if project:
        print("Retrieved project with converted keys:", type(project))
        for i,j in project.items():
            # if i == 'table_dict':
            #     for k,v in j.items():
            #         print(f'{k} : {v}')
                    
            #     continue
            print(f'{i} : {j}')