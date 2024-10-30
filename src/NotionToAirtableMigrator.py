
from pyairtable import Table, Api
from pyairtable.orm import Model, fields as F
from NotionApiHelper import NotionApiHelper
import importlib, json, logging, re, sys, os, datetime
        
'''
IT IS EXTREMELY IMPORTANT THAT EVERY DATABASE BEING MIGRATED HAS A 'Notion record' PROPERTY.

# Config Structure
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


sys.path.append(os.path.join(os.path.dirname(__file__), 'src')) # Add the src directory to the path for imports.
        
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output/logs/NotionToAirtableMigrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def build_airtable_class_headers(airtable_table_name):
    print(f"Building class headers for Airtable table {airtable_table_name}")
    class_name = airtable_table_name.replace(" ", "_") # Removes whitespace and replaces with underscores.
    class_name = re.sub(r'\W+', '', class_name) # Remove any non-alphanumeric characters.
    class_airtable_imports = f'''
from pyairtable import Table
from pyairtable.orm import Model, fields as F
    '''
    
    class_airtable_header = f'class {class_name}(Model):'
    
    header = f'{class_airtable_imports}\n\n{class_airtable_header}\n\n'
    
    print(f"Returning class headers for Airtable table {airtable_table_name}")
    return header
    
def build_airtable_class_meta(airtable_base_id, airtable_table_name):
    print(f"Building class meta for Airtable table {airtable_table_name}")
    
    class_airtable_meta = f'''
    class Meta:
        with open('conf/Airtable_Token.txt', 'r') as file:
            api_key = file.read().strip()
        base_id = '{airtable_base_id}'
        table_name = '{airtable_table_name}'       
    '''
    
    print(f"Returning class meta for Airtable table {airtable_table_name}")
    
    return class_airtable_meta

def build_airtable_class_body(property_map, type_map):
    """
    Constructs the body of an Airtable class based on the provided property and type mappings.
    Args:
        property_map (dict): A dictionary mapping Notion property names to Airtable property names.
        type_map (dict): A dictionary mapping Notion property names to their corresponding types.
    Returns:
        str: A string representing the body of the Airtable class with fields defined according to the mappings.
    """
    
    body = ""
    
    # Iterate through the property map to build the class body.
    for notion_property_name, airtable_property_name in property_map.items():
        
        class_property_name = airtable_property_name.lower().replace(" ", "_") # Convert to lowercase and replace spaces with underscores.
        class_property_name = re.sub(r'\W+', '', class_property_name) # Remove any non-alphanumeric characters.
        
        class_property_map = { # Maps notion property types to Airtable field types for class construction.
            'checkbox': f'    {class_property_name} = F.CheckboxField(\'{airtable_property_name}\')',
            'created_by': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'created_time': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'email': f'    {class_property_name} = F.EmailField(\'{airtable_property_name}\')',
            'number': f'    {class_property_name} = F.NumberField(\'{airtable_property_name}\')',
            'phone_number': f'    {class_property_name} = F.PhoneNumberField(\'{airtable_property_name}\')',
            'people': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'url': f'    {class_property_name} = F.UrlField(\'{airtable_property_name}\')',
            'last_edited_time': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'select': f'    {class_property_name} = F.SelectField(\'{airtable_property_name}\')',
            'status': f'    {class_property_name} = F.SelectField(\'{airtable_property_name}\')',
            'formula': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'unique_id': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'rich_text': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'title': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'relation': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'date': f'    {class_property_name} = F.DateField(\'{airtable_property_name}\')',
            'files': f'    {class_property_name} = F.UrlField(\'{airtable_property_name}\')',
            'last_edited_by': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')',
            'multi_select': f'    {class_property_name} = F.MultipleSelectField(\'{airtable_property_name}\')',
            'rollup': f'    {class_property_name} = F.TextField(\'{airtable_property_name}\')'    
        }
        
        # Fetch the property type and add the corresponding field to the class body.
        prop_type = type_map[notion_property_name]
        print(f"{class_property_map[prop_type]}")
        body += f'{class_property_map[prop_type]}\n'
        
    logger.info(f"Returning class body for Airtable table {airtable_table_name}")
    
    return body
    
def construct_class(property_map, airtable_base_id, airtable_table_name, type_map):
    class_code = f'# THIS IS A GENERATED FILE FROM NotionToAirtableMigrator.py\n\n'
    class_code += f'{build_airtable_class_headers(airtable_table_name)}\n'
    class_code += f'{build_airtable_class_body(property_map, type_map)}\n'
    class_code += f'{build_airtable_class_meta(airtable_base_id, airtable_table_name)}\n\n'
    
    logger.info(f"Returning class string for Airtable table {airtable_table_name}")
    return class_code 

def import_new_class(airtable_table_name):
    try:
        module = importlib.import_module(f'NTAM_{airtable_table_name}')
    except ModuleNotFoundError:
        logger.error(f"Error Importing Class {airtable_table_name} not found in NTAM_{airtable_table_name}.py")
        return None
    
    class_name = airtable_table_name.replace(" ", "_")
    return getattr(module, class_name)   
        
def build_type_map(property_map, db_id):
    
    print(f"Building type map for database {db_id}")
    type_map = {}
    records = fetch_notion_data(db_id)
    if records is None:
        print(f"No records found for database {db_id}, skipping to next database.")
        return None, None
    record = records[0] # We only need one record to get the property types
    for property_name in property_map:
        if property_name not in type_map:
            print(f"Adding property {property_name} to the type map as {record['properties'][property_name]['type']}.")
            type_map[property_name] = record['properties'][property_name]['type']
       
    print(f"Type map built for database {db_id}\n{type_map}")     
    return type_map, records
    
def fetch_notion_data(db_id):
    print(f"Fetching all records from the Notion database with ID '{db_id}'")
    return notion_helper.query(db_id)

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

    print(f"Checking for table {airtable_table_name} in Airtable base {airtable_base_id}.")
    airtable_bases = api.bases()
    stop_script = True # Finding a match will switch this to False.
    
    for Base in airtable_bases:
        print(f"Base ID: {Base.id}")
        if Base.id == airtable_base_id:
            print(f"Base ID {airtable_base_id} found in Airtable.")
            current_base = Base
            stop_script = False
            break
    
    if stop_script:
        logger.error(f"Base ID {airtable_base_id} not found in Airtable, skipping to next record.")
        return None
    
    airtable_tables = current_base.tables()
    print(airtable_tables)
    for Table in airtable_tables:
        print(f"Table Name: {Table.name}")
        if Table.name == airtable_table_name:
            print(f"Table {airtable_table_name} found in Airtable.")
            return Table

    print(f"Table {airtable_table_name} not found in Airtable, creating table.")
    logger.info(f"Table {airtable_table_name} not found in Airtable, creating empty table.")
    new_table = current_base.create_table(airtable_table_name, fields=[{'name': 'Name', 'type': 'singleLineText'}]) 
    print(f"Table {airtable_table_name} created in Airtable.")
    
    return new_table


'''
Airtable Field Types:
"singleLineText" | "email" | "url" | "multilineText" | "number" | "percent" | "currency" | "singleSelect" | "multipleSelects" | "singleCollaborator" | "multipleCollaborators" | "multipleRecordLinks" | "date" | "dateTime" | "phoneNumber" | "multipleAttachments" | "checkbox" | "formula" | "createdTime" | "rollup" | "count" | "lookup" | "multipleLookupValues" | "autoNumber" | "barcode" | "rating" | "richText" | "duration" | "lastModifiedTime" | "button" | "createdBy" | "lastModifiedBy" | "externalSyncSource" | "aiText"
'''

def convert_type_map(type_map):
    print(f"Converting type map from Notion to Airtable format.")
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
        
    print(f"Type map converted to Airtable format.\n{new_map}")
    return new_map


def repair_table_properties(air_table, property_map, type_map):
    """
    Repairs and updates the properties of an Airtable table based on the provided property and type mappings.
    Args:
        air_table (Airtable): The Airtable table object to be updated.
        property_map (dict): A dictionary mapping Notion property names to Airtable property names.
        type_map (dict): A dictionary mapping Notion property types to Airtable property types.
    Returns:
        tuple: A tuple containing the updated Airtable table object and a list of relation fields added.
    Raises:
        AirtableApiError: If there is an error interacting with the Airtable API.
    Example:
        property_map = {
            'NotionProperty1': 'AirtableProperty1',
            'NotionProperty2': 'AirtableProperty2'
        }
        type_map = {
            'NotionProperty1': 'singleLineText',
            'NotionProperty2': 'number'
        }
        updated_table, relations = repair_table_properties(air_table, property_map, type_map)
    """ 
    
    print(f"Assessing properties for Airtable table {air_table.name}")
    schema = air_table.schema()
    existing_field_list = []
    relation_list = []

    # Add a link field for each relation property to be linked together later. The data transfer later will also add the relation to the record as a string for redundency.
    for name, type in type_map.items():
        if type == 'relation':
            relation_list.append(name)
    print(f"Relation list: {relation_list}")
    
    type_map = convert_type_map(type_map) # Converts typing from Notion format to Airtable format.
    
    # Check for existing fields in the table
    for field in schema.fields: 
        if field.name in property_map.values():
            print(f"Property {field.name} already exists in Airtable table {air_table.name}")
            existing_field_list.append(field.name)
    
    # Add any missing fields to the table
    for notion_property, airtable_property in property_map.items():
        if airtable_property not in existing_field_list:
            print(f"Adding property {airtable_property} to Airtable table {air_table.name}")
            logger.info(f"Adding property {airtable_property} to Airtable table {air_table.name}")
            air_table.create_field(airtable_property, type_map[notion_property])
            
    print(f"Properties assessed and repaired for Airtable table {air_table.name}")
    return air_table, relation_list

def create_airtable_records(airtable_record_list, notion_db_records, property_map, type_map, Airtable_Class, notion_db_id):
    # Iterate through the Notion DB records to create Airtable records
    for page in notion_db_records:
        print(f"Processing record {page['id']} from database {notion_db_id}")
        
        # Create an instanced Airtable Table Class
        airtable_record = Airtable_Class()
        
        # Iterate through the property map
        print(f"Itterating through property map for record {page['id']}")
        for notion_property_name, airtable_property_name in property_map.items():
            class_property_name = airtable_property_name.lower().replace(" ", "_")
            class_property_name = re.sub(r'\W+', '', class_property_name) # Remove any non-alphanumeric characters.
            prop_type = type_map[notion_property_name]
            
            # Fetch the Notion property value and assign it to the Airtable record
            if notion_property_name in page['properties']:
                print(f"Property {notion_property_name} found in record {page['id']}")
                notion_property_value = notion_helper.return_property_value(page['properties'][notion_property_name])
                
                # Convert the date to a string in a date format for airtable.
                if prop_type == 'date' and notion_property_value:
                    if isinstance(notion_property_value, str):
                        notion_property_value = datetime.datetime.strptime(notion_property_value, '%Y-%m-%d')
                
                # Convert the array types to a string for airtable.
                array_types_to_string = ['relation', 'rollup', 'people', 'files']
                if prop_type in array_types_to_string and notion_property_value:
                    notion_property_value = str(notion_property_value)
                
                if notion_property_value == []:
                    notion_property_value = None
                    
                print(f"Setting property {class_property_name} to {notion_property_value}")
                setattr(airtable_record, class_property_name, notion_property_value)
                
            else:
                print(f"Setting property {class_property_name} to None")
                setattr(airtable_record, class_property_name, None)
                
        # Add the record to a list of records to batch save
        logger.info(f"Adding record {page['id']} to batch save list for table {airtable_table_name}.")
        airtable_record_list.append(airtable_record) # List of objects.
    return airtable_record_list


def find_relation_database(relations, relation_list, notion_db_id):
    print(f"Finding related databases for database {notion_db_id}")
    for notion_property in relation_list:
        print(f"Finding related database for property {notion_property}")
        index = 0
        related_page = None
        
        while index < len(notion_db_records) or index < 0: # Iterate through the records until we find a page containing relation data.
            if notion_property in notion_db_records[index]['properties']:
                print(f"Property {notion_property} exists in record {notion_db_records[index]['id']}: {notion_db_records[index]['properties'][notion_property]}")
                rel_prop_value = notion_helper.return_property_value(notion_db_records[index]['properties'][notion_property]) # Returns a list of IDs
            else: # Property does not exist.
                continue
            
            if rel_prop_value: # Property has data.
                print(f"Relation data found for property: {rel_prop_value}")
                related_page = notion_helper.get_page(rel_prop_value[0]) # Fetch a related page so we can get the DB_ID.
                break # We found the related page, break the loop.
            
            # No relation data found, continue to the next record.
            print(f"Property {notion_property} value is: {rel_prop_value}")
            index += 1
            
        if related_page: # Map what database ID the property relates to.
            related_db_id = related_page['parent']['database_id']
            
            logger.info(f"Mapping property {notion_property} to database {related_db_id}")
            
            # Add the relation mapping to the relations dictionary. Notion property: Database ID of related table.
            relations[notion_db_id]['relation_mapping'] = {notion_property: related_db_id}
            
        else: # No relation data found, set the related database ID to None.
            logger.info(f"Could not find related database for property {notion_property}. Mapping to None.")
            relations[notion_db_id]['relation_mapping'] = {notion_property: None}
            
    print(f"Returning relations:\n{relations}")
    return relations           

def make_relation_links(notion_db_id, relations, relation_map, airtable_record_list, property_map):
    """
    Establishes relation links between Notion and Airtable records based on the provided mappings.
    Args:
        notion_db_id (str): The ID of the Notion database.
        relations (dict): A dictionary containing relation mappings between Notion properties and related database IDs.
        relation_map (dict): A dictionary mapping related database IDs to their corresponding Airtable table names and base IDs.
        airtable_record_list (list): A list of Airtable record objects to be updated with relation links.
        property_map (dict): A dictionary mapping Notion properties to their corresponding Airtable field names.
    Returns:
        list: The updated list of Airtable record objects with established relation links.
    """
    
    logger.info(f"Checking for relation properties in database {notion_db_id}")
    for notion_property, related_db_id in relations[notion_db_id]['relation_mapping'].items():
        
        # Both tables are built, we can link the records.
        if related_db_id and related_db_id in relation_map:
            print(f"Both tables built for relation property {notion_property}.")
            
            class_property_name = property_map[notion_property].lower().replace(" ", "_")
            class_property_name = re.sub(r'\W+', '', class_property_name) # Remove any non-alphanumeric characters.              
            related_table_name = relation_map[related_db_id]['airtable_table_name']
            related_base_id = relation_map[related_db_id]['airtable_base_id']
            related_table = api.table(related_base_id, related_table_name)
            add_field = True
            
            # Fetch all records from the related table. Dictionary.
            print(f"Fetching all records from the related table {related_table_name}")
            related_records = related_table.all() 
            
            # Iterate through the records to find the related record.
            print(f"Itterating through records to link relation property {notion_property}")
            for index, current_record in enumerate(airtable_record_list): # current_record is an object.
                # Fetch the related record from the current record's property.
                for related_record in related_records['records']: # related_record is a dictionary.
                    
                    # If the related record (String of Notion record) is in the current record's property (String of List of Notion ids)
                    if related_record['fields']['Notion record'] in getattr(current_record, class_property_name):
                        print(f"Related record found for relation property {notion_property}")
                        
                        # Set the relation property to the related record's Airtable ID.
                        print(f"Setting property REL__{class_property_name} to {related_record['id']}")
                        logging.info(f"Setting property REL__{class_property_name} to {related_record['id']}")
                        setattr(current_record, f'REL__{class_property_name}', related_db_id)
                        
                        # Save the record back to the list.
                        print(f"Adding record {current_record} to batch save list.")
                        airtable_record_list[index] = current_record
    return airtable_record_list



'''
This will be a 4 step program to get Airtable on track. There's a few things where I'm aiming for simplicity over efficiency.
 1) Check the Airtable table for the required properties, generating any that are missing.
 2) Create a class for the Airtable table with the required properties.
 3) Iterate through the Notion database records, creating and saving a new Airtable record for each.
 4) Iterate back through all records to make any necessary links after all tables are built.
 '''
if __name__ == "__main__":
    
    # Initialize the Notion API Helper
    notion_helper = NotionApiHelper()
    
    # Initialize the Airtable API
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
        logger.info(f"Processing database {database}")
        
        airtable_record_list = [] # List of Airtable records to batch save.
        airtable_table_name = database['airtable_table_name']
        airtable_base_id = database['airtable_base_id']
        notion_db_id = database['notion_db_id']
        property_map = database['property_map'] # Notion to Airtable property mapping.
        self_relation = False # If the database is self-referential, this will be set to True.
        
        relations = {notion_db_id: {}} # This will be used to store the relation properties and what they relate to.
        relations[notion_db_id] = { 
            'airtable_table_name':airtable_table_name,
            'airtable_base_id':airtable_base_id,
            'relation_mapping':{}
        }

        # Create the table if it does not exist, also will load the table object to check for properties.
        current_table = check_table_exists(airtable_base_id, airtable_table_name)
        if current_table is None:
            print(f"Table {airtable_table_name} not found in Airtable, skipping to next database.")
            logger.error(f"Table {airtable_table_name} not found in Airtable, skipping to next database.")
            continue
        
        # Build the type map here, return the notion DB query as a byproduct for later use.
        type_map, notion_db_records = build_type_map(property_map, notion_db_id)
        
        # Repair the table properties, gather a list of relation properties for later.
        current_table, relation_list = repair_table_properties(current_table, property_map, type_map)
        
        # Map the relation properties to their related database ID
        relations = find_relation_database(relations, relation_list, notion_db_id)
        
        # Build the class
        class_code = construct_class(property_map, airtable_base_id, airtable_table_name, type_map)
        
        # Write the class to a file
        with open(f'src/NTAM_{airtable_table_name}.py', 'w') as file:
            file.write(class_code)
        logger.info(f"Class {airtable_table_name} created as NTAM_{airtable_table_name}.py")
        
        # Import the new class
        Airtable_Class = import_new_class(airtable_table_name)
        
        if Airtable_Class is None:
            logger.error(
                f"Class {airtable_table_name} not imported from NTAM_{airtable_table_name}.py, skipping to next database."
                )
            continue # Skip to the next database if the class is not imported.
        logger.info(f"Class {airtable_table_name} imported from NTAM_{airtable_table_name}.py")
        
        # Create the Airtable records
        airtable_record_list = create_airtable_records(
            airtable_record_list, notion_db_records, property_map, type_map, Airtable_Class, notion_db_id
        )
        
        # If there are relation properties, check if both tables have been built.
        airtable_record_list = make_relation_links(
            notion_db_id, relations, relation_map, airtable_record_list, property_map
        )
            
        # Batch save the records to the table.
        print(f"Batch saving records to Airtable table {airtable_table_name}")
        Airtable_Class.batch_save(airtable_record_list)
        logger.info(f"Records batch saved to Airtable table {airtable_table_name}")
        
        
    # Write the relation_map to a JSON file
    relation_map_file_path = 'output/relation_map.json'
    print(f"Writing relation map to {relation_map_file_path}")
    with open(relation_map_file_path, 'w') as relation_map_file:
        json.dump(relation_map, relation_map_file, indent=4)
    logger.info(f"Relation map written to {relation_map_file_path}")

  