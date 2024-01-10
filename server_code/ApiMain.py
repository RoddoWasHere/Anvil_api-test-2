import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.http import HttpError
import json
from .SchemaShaper import *
from .DataManagerModel import *

# --- Form callable ----

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


# --- API ----

@anvil.server.http_endpoint('/get_all_by_type/:type_name', methods=["GET"], enable_cors=True)
def list_data_handler(type_name, **q):
  got_schema = app_tables.schema_table.get(name=type_name)
  all_rows = app_tables.data_table.search(schema=got_schema)
  results = []

  for row in all_rows:
    row_tp = row['data']
    row_tp["id"] = row.get_id()
    results.append(row_tp)
  return json.dumps(results)


@anvil.server.http_endpoint('/get_data/:id', methods=["POST"], enable_cors=True)
def get_data_handler(id, **q):
  try:
    query_schema = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")

  got_data = DataManagerModel.get_data_by_id(id)

  if got_data:
    return got_data
  return anvil.server.HttpResponse(404, "No such data with id")


@anvil.server.http_endpoint('/set_data/:id', methods=["POST"], enable_cors=True)
def set_data_handler(id, **q):
  try:
    req_body = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")

  if not req_body:
    return anvil.server.HttpResponse(400, "No data provided")

  got_data = DataManagerModel.set_data_by_id(id, req_body)
  if got_data:
    return got_data
  return anvil.server.HttpResponse(404, "No such data with id")


@anvil.server.http_endpoint('/add_data/:type_name', methods=["POST"], enable_cors=True)
def add_data_handler(type_name, **q):
  try:
    req_body = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")
  
  got_schema = DataManagerModel.get_schema_by_name(type_name)
  if not got_schema:
    return anvil.server.HttpResponse(400, "No such schema exists")

  if not req_body:
    return anvil.server.HttpResponse(400, "No data provided")

  got_data = DataManagerModel.add_data(type_name, req_body)
  if got_data:
    return got_data
  return anvil.server.HttpResponse(404, "No such data with id")


@anvil.server.http_endpoint('/delete_data/:id', methods=["POST"], enable_cors=True)
def delete_data_handler(id, **q):
  data_row = app_tables.data_table.get_by_id(id)
  if data_row:
    data_row.delete()
    return id

  return None
  
  