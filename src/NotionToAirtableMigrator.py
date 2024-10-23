
from pyairtable import Table, Api
from pyairtable.orm import Model, fields as F
from NotionApiHelper import NotionApiHelper
import importlib, json, logging
        
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output/logs/NotionToAirtableMigrator.log"),
        logging.StreamHandler()
    ]
)

lumberjack = logging.getLogger(__name__)

def build_airtable_class_headers(airtable_table_name):
    class_airtable_imports = f'''
    from pyairtable import Table
    from pyairtable.orm import Model, fields as F
    '''
    
    class_airtable_header = f'class {airtable_table_name}(Model):'
    
    header = f'{class_airtable_imports}\n\n{class_airtable_header}\n\n'
    
    return header
    
def build_airtable_class_meta(airtable_base_id, airtable_table_name):
    class_airtable_meta = f'''
        class Meta:
            with open('conf/Airtable_Token.txt', 'r') as file:
                api_key = file.read().strip()
            base_id = '{airtable_base_id}'
            table_name = '{airtable_table_name}'       
    '''
    return class_airtable_meta

def build_airtable_class_body(property_map, type_map):
    body = ""
    for notion_property_name, airtable_property_name in property_map.items():
        class_property_name = airtable_property_name.lower().replace(" ", "_") # Hey remember that this is how the variables are structured for later!
        class_property_map = {
            'checkbox': f'    {class_property_name} = F.CheckboxField({airtable_property_name})',
            'created_by': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'created_time': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'email': f'    {class_property_name} = F.EmailField({airtable_property_name})',
            'number': f'    {class_property_name} = F.NumberField({airtable_property_name})',
            'phone_number': f'    {class_property_name} = F.PhoneNumberField({airtable_property_name})',
            'people': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'url': f'    {class_property_name} = F.UrlField({airtable_property_name})',
            'last_edited_time': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'select': f'    {class_property_name} = F.SelectField({airtable_property_name})',
            'status': f'    {class_property_name} = F.SelectField({airtable_property_name})',
            'formula': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'unique_id': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'rich_text': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'title': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'relation': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'date': f'    {class_property_name} = F.DateField({airtable_property_name})',
            'files': f'    {class_property_name} = F.UrlField({airtable_property_name})',
            'last_edited_by': f'    {class_property_name} = F.TextField({airtable_property_name})',
            'multi_select': f'    {class_property_name} = F.MultipleSelectField({airtable_property_name})',
            'rollup': f'    {class_property_name} = F.TextField({airtable_property_name})'    
        }
        
        prop_type = type_map[class_property_name]
        body += f'{class_property_map[prop_type]}\n'
        
    return body
        
def build_type_map(property_map, db_id):
    type_map = {}
    records = fetch_notion_data(db_id)
    if records is None:
        return None, None
    record = records[0] # We only need one record to get the property types
    for property_name in record['properties']:
        if property_name not in property_map:
            property_map[property_name] = record['properties'][property_name]['type']
            
    return type_map, records
                
    
def construct_class(property_map, airtable_base_id, airtable_table_name, type_map):
    class_code = f'# THIS IS A GENERATED FILE FROM NotionToAirtableMigrator.py\n\n'
    class_code += f'{build_airtable_class_headers(airtable_table_name)}\n'
    class_code += f'{build_airtable_class_body(property_map, type_map)}\n'
    class_code += f'{build_airtable_class_meta(airtable_base_id, airtable_table_name)}\n\n'
    
    return class_code


def fetch_notion_data(db_id):
    print(f"Fetching all records from the Notion database with ID '{db_id}'")
    return notion_helper.query(db_id)

    
def import_new_class(airtable_table_name):
    try:
        module = importlib.import_module(f'src/NTAM_{airtable_table_name}')
    except ModuleNotFoundError:
        return None
    return getattr(module, airtable_table_name)
      

def check_table_exists(airtable_base_id, airtable_table_name):
    """
    Checks if a specified table exists within a given Airtable base.
    Args:
        airtable_base_id (str): The ID of the Airtable base to search within.
        airtable_table_name (str): The name of the table to search for.
    Returns:
        Table or None: Returns the table object if found, otherwise returns None.
    Logs:
        Logs an error message if the base or table is not found.
    """
    
    airtable_bases = api.bases()
    stop_script = True # Finding a match will switch this to False.
    for Base in airtable_bases:
        if Base.id == airtable_base_id:
            current_base = Base
            stop_script = False
    
    if stop_script:
        print(f"Base ID {airtable_base_id} not found in Airtable, skipping to next record.")
        lumberjack.error(f"Base ID {airtable_base_id} not found in Airtable, skipping to next record.")
        return None
    
    stop_script = True # Finding a match will switch this to False.
    airtable_tables = current_base.tables()
    print(airtable_tables)
    for Table in airtable_tables:
        if Table.name == airtable_table_name:
            return Table


    print(f"Table {airtable_table_name} not found in Airtable, creating table.")
    lumberjack.info(f"Table {airtable_table_name} not found in Airtable, creating empty table.")
    new_table = current_base.create_table(airtable_table_name, fields=[{'name': 'Name', 'type': 'singleLineText'}]) 
    
    return new_table


'''
Airtable Field Types:
"singleLineText" | "email" | "url" | "multilineText" | "number" | "percent" | "currency" | "singleSelect" | "multipleSelects" | "singleCollaborator" | "multipleCollaborators" | "multipleRecordLinks" | "date" | "dateTime" | "phoneNumber" | "multipleAttachments" | "checkbox" | "formula" | "createdTime" | "rollup" | "count" | "lookup" | "multipleLookupValues" | "autoNumber" | "barcode" | "rating" | "richText" | "duration" | "lastModifiedTime" | "button" | "createdBy" | "lastModifiedBy" | "externalSyncSource" | "aiText"
'''

def convert_type_map(type_map):
    new_map = {}
    class_property_map = { # This map intentionally maps properties incorrectly to allow for data transfer.
    'checkbox': 'checkbox',
    'created_by': f'singleLineText',
    'created_time': f'singleLineText',
    'email': f'email',
    'number': f'number',
    'phone_number': f'phoneNumber',
    'people': f'singleLineText',
    'url': f'url',
    'last_edited_time': f'singleLineText',
    'select': f'singleSelect',
    'status': f'singleSelect',
    'formula': f'multilineText',
    'unique_id': f'singleLineText',
    'rich_text': f'multilineText', # I know there's a rich text property, we're not transferring it.
    'title': f'singleLineText',
    'relation': f'singleLineText',
    'date': f'date',
    'files': f'url',
    'last_edited_by': f'singleLineText',
    'multi_select': f'multipleSelects',
    'rollup': f'multilineText'    
}
    for key, value in type_map.items():
        new_map[key] = class_property_map[value]
    return new_map


def repair_table_properties(air_table, property_map, type_map):
    schema = air_table.schema()
    existing_field_list = []

    
    for name, type in type_map.items():
        if type == 'relation':
            air_table.create_field(f"REL__{name}", 'multipleRecordLinks')
            relation_list.append(name)
    
    type_map = convert_type_map(type_map) # Converts typing from Notion format to Airtable format.
    
    # Check for existing fields in the table
    for field in schema.fields: 
        if field.name in property_map.values():
            existing_field_list.append(field.name)
    
    # Add any missing fields to the table
    for notion_property, airtable_property in property_map.items():
        if airtable_property not in existing_field_list:
            print(f"Adding property {airtable_property} to Airtable table {air_table.name}")
            lumberjack.info(f"Adding property {airtable_property} to Airtable table {air_table.name}")
            air_table.create_field(airtable_property, type_map[notion_property])
    return air_table, relation_list

'''
This will be a 4 step program. There's a few things where I'm aiming for simplicity over efficiency.
 1) Check the Airtable table for the required properties, generating any that are missing.
 2) Create a class for the Airtable table with the required properties.
 3) Iterate through the Notion database records, creating and saving a new Airtable record for each.
 4) Iterate back through all records to make any necessary links after all tables are built.
 '''
if __name__ == "__main__":
    notion_helper = NotionApiHelper()
    with open('conf/Airtable_Token.txt', 'r') as file:
        api_key = file.read().strip()
    api = Api(api_key)
    
    # Load the configuration file
    with open('conf/NotionAirtableMigrationConfig.json', 'r') as config_file:
        config = json.load(config_file)

    # Used to store the relation properties and what they relate to.
    relation_map = []
    
    # Iterate through the configuration file
    for database in config:
        airtable_record_list = []
        airtable_table_name = database['airtable_table_name']
        airtable_base_id = database['airtable_base_id']
        notion_db_id = database['notion_db_id']
        property_map = database['property_map']
        
        relation = {}
        relation['airtable_table_name'] = notion_db_id

        
        # Create the table if it does not exist, also will load the table object to check for properties.
        current_table = check_table_exists(airtable_base_id, airtable_table_name)
        if current_table is None:
            lumberjack.error(f"Table {airtable_table_name} not found in Airtable, skipping to next database.")
            continue
        
        # Build the type map here, return the notion DB query as a byproduct for later use.
        type_map, notion_db_records = build_type_map(property_map, notion_db_id)
        
        # Repair the table properties, gather a list of relation properties for later.
        current_table, relation_list = repair_table_properties(current_table, property_map, type_map)
        
        # Map the relation properties to their related database ID
        for notion_property in relation_list:
            relation[property_map[notion_property]] = {'notion_property':notion_property}
            index = 0
            related_page = None
            while index < len(notion_db_records) or index < 0: # Iterate through the records until we find a page containing relation data.
                rel_prop_value = notion_helper.return_property_value(notion_db_records[index]['properties'][notion_property])
                if rel_prop_value:
                    related_page = notion_helper.get_page(rel_prop_value[0]['id'])
                    break # We found the related page, break the loop.
                index += 1
            if related_page: 
                relation[property_map[notion_property]]['related_db_id'] = related_page['parent']['database_id']
            else: # No relation data found, set the related database ID to None.
                relation[property_map[notion_property]]['related_db_id'] = None

        
        # Build the class
        class_code = construct_class(property_map, airtable_base_id, airtable_table_name, type_map)
        
        # Write the class to a file
        with open(f'src/NTAM_{airtable_table_name}.py', 'w') as file:
            file.write(class_code)
        lumberjack.info(f"Class {airtable_table_name} created as NTAM_{airtable_table_name}.py")
        
        # Import the class
        Airtable_Class = import_new_class(airtable_table_name)
        if Airtable_Class is None:
            lumberjack.error(f"Class {airtable_table_name} not imported from NTAM_{airtable_table_name}.py, skipping to next database.")
            continue
        lumberjack.info(f"Class {airtable_table_name} imported from NTAM_{airtable_table_name}.py")
        
        # Iterate through the Notion DB records
        for page in notion_db_records:
            
            # Create an instanced Airtable Table Class
            airtable_record = Airtable_Class()
            
            # Iterate through the property map
            for notion_property_name, airtable_property_name in property_map.items():
                class_property_name = airtable_property_name.lower().replace(" ", "_")
                prop_type = type_map[notion_property_name]
                # Fetch the Notion property value and assign it to the Airtable record
                if notion_property_name in page['properties']:
                    notion_property_value = notion_helper.return_property_value(page['properties'][notion_property_name])
                    if prop_type == 'date' and notion_property_value:
                        notion_property_value = notion_property_value.strftime('%Y-%m-%d')
                
                    setattr(airtable_record, class_property_name, notion_property_value)
                else:
                    setattr(airtable_record, class_property_name, None)
                    
            # Add the record to a list of records to batch save
            airtable_record_list.append(airtable_record)
            
        # Batch save the records to the table.
        Airtable_Class.batch_save(airtable_record_list)
    pass


''' # Config Structure
[
    {
    'base_id': base_id,
    'airtable_table_name': table_name,
    'notion_db_id': db_id,
    'property_map': {
        'notion_property_name': 'airtable_property_name',
        'notion_property_name': 'airtable_property_name',
        'notion_property_name': 'airtable_property_name',
        'notion_property_name': 'airtable_property_name',
        etc...
    }
    }   
]
'''    