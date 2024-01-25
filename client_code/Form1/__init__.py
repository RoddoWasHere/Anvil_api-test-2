from ._anvil_designer import Form1Template
from anvil import *
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import json

class Form1(Form1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.

    self.schema_drop_down.items = anvil.server.call("get_schema_names")
    self.schema_drop_down.add_event_handler('change', self.upate_schema_rt)
    
    schema_obj = anvil.server.call("get_schema", "todoListItem")
    self.rich_text_schema_preview.content = "```JSON\n" + json.dumps(schema_obj, indent=4) + "\n```"
    
    self.init_components(**properties)

    while not anvil.users.login_with_form():
      pass
  
    # Any code you write here will run before the form opens.
  
  def upate_schema_rt(self, sender, event_name):
    print("got update?");
    schema_name = self.schema_drop_down.selected_value
    schema_obj = anvil.server.call("get_schema", schema_name)
    self.rich_text_schema_preview.content = "```JSON\n" + json.dumps(schema_obj, indent=4) + "\n```"
    # self.rich_text_schema_preview.content = "```JSON\n" + self.to_json_schema() + "\n```"
    # self.rich_text_schema_preview.content = "```JSON\n" + self.to_json_schema() + "\n```"
  
  # def to_json_schema(self):
  #   result = {}
  #   for tp in self.repeating_panel_schema.items:
  #     result[tp["name"]] = ('', "!") [tp["is_required"]] + tp["type_name"]
    
  #   return json.dumps(result, indent=4)