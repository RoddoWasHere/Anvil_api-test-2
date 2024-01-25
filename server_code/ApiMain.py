import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.http import HttpError
import json
from .SchemaShaper import *
from .DataManagerModel import *
# import hashlib
import bcrypt
from datetime import datetime

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


# --- AUTH API ----

class AuthService:
  @staticmethod
  def generate_new_token(user_id: str) -> str:
    d_secs = datetime.now().timestamp()
    enc_string = f"{user_id}:{d_secs}"
    token_tp = bcrypt.hashpw(enc_string.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return token_tp

  @staticmethod
  def get_user_from_token(token = None):
    use_token = token
    if not token:
      use_token = anvil.server.request.headers.get("authorization")
      print("got header auth token?", use_token)
    if use_token:
      got_session = app_tables.user_sessions.get(token=use_token)
      if got_session:
        user = got_session["user"]
        return user
    return None
  
@anvil.server.http_endpoint('/logout', methods=["GET"], enable_cors=True)
def logout_handler(**q):
  user = anvil.users.logout()
  anvil.server.session["authenticated"] = False

@anvil.server.http_endpoint('/login', methods=["POST"], enable_cors=True)
def login_handler(**q):
  user = AuthService.get_user_from_token()
  if user:
    return anvil.server.HttpResponse(200, "Already logged in")
    
  try:
    req_body = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")
  
  if req_body["email"] and req_body["password"]:
    password = req_body["password"]
    email = req_body["email"]
    user = anvil.users.login_with_email(email, password) # ??
    if user:
      token_tp = AuthService.generate_new_token(user.get_id())
      app_tables.user_sessions.add_row(token=token_tp, user=user)
      return {"token": token_tp}
  return anvil.server.HttpResponse(401, "Unauthorized")

# --- SCHEMA API ----

@anvil.server.http_endpoint('/schemas', methods=["GET"], enable_cors=True)
def schemas_handler(**q):
  user = AuthService.get_user_from_token()
  if user:
    schemas = app_tables.schema_table.client_writable(owner=user)
    # TODO: formalize
    result = map(lambda s: {"schema": s["schema"], "name": s["name"], "id": s.get_id()}, schemas.search())
    print(result)
    return list(result)
  return anvil.server.HttpResponse(401, "Unauthorized")

@anvil.server.http_endpoint('/set_schema', methods=["POST"], enable_cors=True)
def set_schema_handler(**q):
  user = AuthService.get_user_from_token()
  if not user:
    return anvil.server.HttpResponse(401, "Unauthorized")
    
  schemas = app_tables.schema_table.client_writable(owner=user)
  
  # TODO: validate...
  

  
  try:
    query_schema = anvil.server.request.body_json
  except json.JSONDecodeError:
    return anvil.server.HttpResponse(400, "Invalid JSON in POST body")
    
  if query_schema.get("id"):
    updated_schema = schemas.get_by_id(query_schema["id"]);

    # Validation: can't modify schema with deps:
    got_schemas_data = app_tables.data_table.search(schema=updated_schema)
    # got_schemas_data = DataManagerModel.get_all_by_type(updated_schema["name"]) #, query_schema)
    print("got_schemas_data", got_schemas_data, len(got_schemas_data))
    
    if got_schemas_data and len(got_schemas_data) > 0:
      return anvil.server.HttpResponse(400, "Cannot change a schema that has linked data")
    
    if not updated_schema:
      return anvil.server.HttpResponse(404, "No such schema with id")
    if query_schema.get("name"):
      updated_schema["name"] = query_schema["name"]
    if query_schema.get("schema"):
      updated_schema["schema"] = query_schema["schema"]
    return {
      "id": updated_schema.get_id(),
      "name": updated_schema["name"],
      "schema": updated_schema["schema"],
    }
  else:
    if not query_schema.get("name") or not query_schema.get("schema"):
      return anvil.server.HttpResponse(400, "Invalid data in POST body")
    
    new_schema = schemas.add_row(name = query_schema["name"], schema = query_schema["schema"])
    return {
      "id": new_schema.get_id(),
      "name": new_schema["name"],
      "schema": new_schema["schema"],
    }
  

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
  
  