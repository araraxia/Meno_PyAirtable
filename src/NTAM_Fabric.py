# THIS IS A GENERATED FILE FROM NotionToAirtableMigrator.py


from pyairtable import Table
from pyairtable.orm import Model, fields as F
    

class Fabric(Model):


    name = F.TextField('Name')
    cost_per_lin_yard = F.NumberField('Cost per lin. Yard')
    fabric_width_in = F.NumberField('Fabric Width (in.)')
    vendors = F.TextField('Vendors')
    notion_record = F.TextField('Notion record')


    class Meta:
        with open('conf/Airtable_Token.txt', 'r') as file:
            api_key = file.read().strip()
        base_id = 'appyRFoHs0KkXgGbl'
        table_name = 'Fabric'       
    

