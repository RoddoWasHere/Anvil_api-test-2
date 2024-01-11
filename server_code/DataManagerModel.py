import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import json
from .SchemaShaper import *

class DataManagerModel:  
  
  @staticmethod
  def get_schema_by_name(name: str):
    got_schema_row = app_tables.schema_table.get(name=name)
    if not got_schema_row:
      return None
    return got_schema_row["schema"]
  
  @staticmethod
  def get_all_by_type(schema_name: str, query_schema: dict = None):
    got_schema_row = app_tables.schema_table.get(name=schema_name)
    all_rows = app_tables.data_table.search(schema=got_schema_row)
    got_schema = got_schema_row["schema"]
    results = []

    for row in all_rows:
      row_tp = row['data']
      row_tp["id"] = row.get_id()
      results.append(row_tp)

    if query_schema:
      # clean the query schema
      cleaned_schema = SchemaShaper.shape(got_schema, query_schema)
      # shape the data
      shaped_results = []
      for data_tp in results:
        shaped_results.append(SchemaShaper.shape(cleaned_schema, data_tp))
      results = shaped_results
    
    return json.dumps(results)
  
  @staticmethod
  def get_data_by_id(id: str, query_schema: dict = None):
    got_data = app_tables.data_table.get_by_id(id)
    if not got_data:
      return None
    got_schema = got_data["schema"]['schema']
  
    if query_schema:
      # clean the query schema
      cleaned_schema = SchemaShaper.shape(got_schema, query_schema)
      # shape the data
      result_shaped = SchemaShaper.shape(cleaned_schema, got_data["data"])
      return json.dumps(result_shaped, indent=2)
    else:
      return json.dumps(got_data["data"], indent=2)
    
    return got_data
  
  @staticmethod
  def set_data_by_id(id: str, data_to_update: dict):
    got_data = app_tables.data_table.get_by_id(id)
    if not got_data:
      return None
    got_schema = got_data["schema"]["schema"]
    
    # shape new data
    new_data = SchemaShaper.shape(got_schema, data_to_update, got_data["data"])

    # validate new data
    if not SchemaShaper.validate(got_schema, new_data):
      return anvil.server.HttpResponse(400, "Validation failed")
    
    #save data
    got_data["data"] = new_data
    return json.dumps(got_data["data"], indent=2)

  @staticmethod
  def add_data(schema_name: str, query_schema: dict = None):
    new_data = {}
    got_schema_row = app_tables.schema_table.get(name=schema_name)
    if not got_schema_row:
      return anvil.server.HttpResponse(400, "No such schema exists")
      
    got_schema = got_schema_row["schema"]
    
    # shape new data
    new_data = SchemaShaper.shape(got_schema, query_schema)

    # validate new data
    if not SchemaShaper.validate(got_schema, new_data):
      return anvil.server.HttpResponse(400, "Validation failed")
    
    #save data
    new_row = app_tables.data_table.add_row(name="??", data=new_data, schema=got_schema_row)
    new_data["id"] = new_row.get_id()
    return json.dumps(new_data, indent=2)
