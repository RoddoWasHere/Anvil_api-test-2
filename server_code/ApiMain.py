import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.http import HttpError
import json
from .SchemaShaper import *

@anvil.server.callable
def get_schema_names():
  result = map(lambda v: v["name"], app_tables.schema_table.search())
  return list(result)



@anvil.server.callable
def get_schemas():
  return app_tables.schema_table.search()


@anvil.server.callable
def get_schema(name):
  schema_row = app_tables.schema_table.get(name=name)
  return schema_row["schema"]


@anvil.server.callable
def get_schema_key_values(name):
  schema_row = app_tables.schema_table.get(name=name)
  schema_data = schema_row["schema"]
  results = []
  for key, value in schema_data.items():
    parsed_type = ShapeType.parse_type(value)
    results.append(
      {
        "name": key, 
        "type_name": parsed_type.shape_type, 
        "is_required": parsed_type.is_required
      }
    )
  return results

# deprecate
@anvil.server.http_endpoint('/list_data', methods=["GET"], enable_cors=True)
def list_data_handler(**q):
  all_rows = app_tables.data_table.search()
  results = []

  # r = anvil.server.HttpResponse()
  # r.headers['access-control-allow-headers'] = 'Content-Type'
  # return r
  
  for row in all_rows:#.items():
    results.append(row["name"])
  return results

@anvil.server.http_endpoint('/get_all_by_type/:type_name', methods=["GET"], enable_cors=True)
def list_data_handler(type_name, **q):
  got_schema = app_tables.schema_table.get(name=type_name)
  all_rows = app_tables.data_table.search(schema=got_schema)
  results = []

  # r = anvil.server.HttpResponse()
  # r.headers['access-control-allow-headers'] = 'Content-Type'
  # return r
  
  for row in all_rows:#.items():
    row_tp = row['data']
    row_tp["id"] = row.get_id()
    results.append(row_tp)
  return json.dumps(results)


@anvil.server.http_endpoint('/get_data/:id', methods=["POST"], enable_cors=True)
def get_data_handler(id, **q):
  got_data = app_tables.data_table.get_by_id(id)
  got_schema = got_data["schema"]['schema']
  
  try:
    query_schema = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")

  # clean provided shape
  
  
  

  
  if got_data is not None:
    if query_schema:
      cleaned_schema = SchemaShaper.shape(got_schema, query_schema)
      result_shaped = SchemaShaper.shape(cleaned_schema, got_data["data"])
      return json.dumps(result_shaped, indent=2)
    else:
      return json.dumps(got_data["data"], indent=2)
  
  return got_data

@anvil.server.http_endpoint('/set_data/:id', methods=["POST"], enable_cors=True)
def set_data_handler(id, **q):
  got_data = app_tables.data_table.get_by_id(id)
  got_schema = got_data["schema"]["schema"]
  try:
    req_body = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")
  
  if req_body:


    # shape new data
    new_data = SchemaShaper.shape(got_schema, req_body, got_data["data"])
    print("got data", new_data)

    # validate new data
    if not SchemaShaper.validate(got_schema, new_data):
      return anvil.server.HttpResponse(400, "Validation failed")
    
    #save data
    got_data["data"] = new_data
  else:
    return anvil.server.HttpResponse(400, "No data provided")
  
  # app_tables.data_table.
  # if got_data is not None:
  #   # exists
  #   got_data["data"] = req_body
  # else:
  #   app_tables.data_table.add_row(name=name, data=req_body)
  return json.dumps(got_data["data"], indent=2)


@anvil.server.http_endpoint('/add_data/:type_name', methods=["POST"], enable_cors=True)
def set_data_handler(type_name, **q):
  # got_data = app_tables.data_table.get_by_id(id)
  # got_data = app_tables.data_table.get_by_id(id)
  # got_schema = got_data["schema"]["schema"]
  new_data = {}
  got_schema_row = app_tables.schema_table.get(name=type_name)
  if not got_schema_row:
    return anvil.server.HttpResponse(400, "No such schema exists")\
    
  got_schema = got_schema_row["schema"]
  
  try:
    req_body = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")
  
  if req_body:

    print("got_schema, req_body?", got_schema, req_body)
    # shape new data
    new_data = SchemaShaper.shape(got_schema, req_body)
    print("got data", new_data)

    # validate new data
    if not SchemaShaper.validate(got_schema, new_data):
      return anvil.server.HttpResponse(400, "Validation failed")
    
    #save data
    app_tables.data_table.add_row(name="??", data=new_data, schema=got_schema_row)
  
  else:
    return anvil.server.HttpResponse(400, "No data provided")
  
  # app_tables.data_table.
  # if got_data is not None:
  #   # exists
  #   got_data["data"] = req_body
  # else:
  #   app_tables.data_table.add_row(name=name, data=req_body)
  return json.dumps(new_data, indent=2)
