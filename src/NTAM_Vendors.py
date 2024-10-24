# THIS IS A GENERATED FILE FROM NotionToAirtableMigrator.py


from pyairtable import Table
from pyairtable.orm import Model, fields as F
    

class Vendors(Model):


    name = F.TextField('Name')
    notes = F.TextField('Notes')
    primary_email = F.EmailField('Primary Email')
    main_phone = F.PhoneNumberField('Main Phone')
    website = F.UrlField('Website')
    address = F.TextField('Address')
    notion_record = F.TextField('Notion record')
    fabric = F.TextField('Fabric')


    class Meta:
        with open('conf/Airtable_Token.txt', 'r') as file:
            api_key = file.read().strip()
        base_id = 'appyRFoHs0KkXgGbl'
        table_name = 'Vendors'       
    

