import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.http import HttpError
import json
from .SchemaShaper import *
from .DataManagerModel import *

"""
Main entry point: form callable and API endpoints (application layer)
"""

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


# --- SCHEMA API ----

@anvil.server.http_endpoint('/schemas', methods=["GET"], enable_cors=True)
def schema_handler(**q):
  user = anvil.users.get_user();
  return user

@anvil.server.http_endpoint('/logout', methods=["GET"], enable_cors=True)
def logout_handler(**q):
  user = anvil.users.logout()

@anvil.server.http_endpoint('/login', methods=["POST"], enable_cors=True)
def login_handler(**q):
  try:
    req_body = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")
  
  if req_body["email"] and req_body["password"]:
    password = req_body["password"]
    email = req_body["email"]
    try:
      user = anvil.users.login_with_email(email, password)
      return anvil.server.HttpResponse(200, "Success")
    except AuthenticationFailed:
      return anvil.server.HttpResponse(401, "Unauthorized")
    
  return anvil.server.HttpResponse(401, "Unauthorized")
  # anvil.server.session["authenticated"] = True

# --- DATA API ----

@anvil.server.http_endpoint('/get_all_by_type/:type_name', methods=["POST", "GET"], enable_cors=True)
def get_all_by_type_handler(type_name, **q):
  got_schema = DataManagerModel.get_schema_by_name(type_name)
  if not got_schema:
    return anvil.server.HttpResponse(400, "No such schema exists")
  
  try:
    query_schema = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")

  results = DataManagerModel.get_all_by_type(type_name, query_schema)
  if not results:
    return None
  return results


@anvil.server.http_endpoint('/get_data/:id', methods=["POST", "GET"], enable_cors=True)
def get_data_handler(id, **q):
  try:
    query_schema = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")

  got_data = DataManagerModel.get_data_by_id(id, query_schema)

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
  
  