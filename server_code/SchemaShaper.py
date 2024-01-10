import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from typing import Callable
from datetime import datetime
import re
from .LL1Parser import *


class TypeParseResult:
  is_required: bool
  shape_type: str
  is_array: bool

  def __init__(self, is_required, shape_type, is_array):
    self.is_required = is_required
    self.shape_type = shape_type
    self.is_array = is_array


# create schema type parser
parser_tokens = [
  ParserToken("is_required", re.compile('(!|)'), lambda s, r: (s == '!')),
  ParserToken("type_name", re.compile('([a-z]|[A-Z])+'), lambda s, r: s),  
  ParserToken("is_array", re.compile('(\[\]|)'), lambda s, r: (s =='[]')), 
]
schema_type_name_parser = LL1Parser(parser_tokens)


class ShapeType:
  def __init__(self, validator):
    self.validator = validator
  
  def validate(self, value):
    return self.validator(value)

  @staticmethod
  def parse_type(type_string):
    # is_required = re.match(r'^!', type_string) is not None
    # shape_type = re.search('\w+', type_string)[0]
    # is_array = False
    res = schema_type_name_parser.parse(type_string)
    if not res:
      return None
    is_required = res["is_required"]
    type_name = res["type_name"]
    is_array = res["is_array"]
    return TypeParseResult(is_required, type_name, is_array)


class ShapeTypeBasic(ShapeType):
  def __init__(self, shape_type: type):
    self.shape_type = shape_type
  
  def validate(self, value):
    return isinstance(value, self.shape_type)


class ShapeTypeBasicCompound(ShapeType):
  def __init__(self, types: [type]):
    self.types = types

  def validate(self, value):  
    for t in self.types:
      if isinstance(value, t):
        return True
    return False


shape_type_lookup = {
  "string": ShapeTypeBasic(str),
  "number": ShapeTypeBasicCompound([int, float, complex]),
  "boolean": ShapeTypeBasic(bool),
  "null": ShapeType(lambda value: value is None),

  # "Array": ShapeTypeBasicCompound([list, tuple, range]),
  # "Date": ShapeTypeBasic(datetime),
}


class SchemaShaper:

  @staticmethod
  def validate(shape: dict, data: dict):
    # TODO: provide reason for failure
    for key, s_value in shape.items():
      # parse the type syntax
      shape_type_parsed = ShapeType.parse_type(s_value)
      if shape_type_parsed is None:
        return False
      
      shape_type_name = shape_type_parsed.shape_type
      shape_type_required = shape_type_parsed.is_required
      shape_type_is_array = shape_type_parsed.is_array
      shape_type = shape_type_lookup[shape_type_name]

      if shape_type is None:
        return False

      if not key in data:
        if not shape_type_required:
          continue
        else:
          return False
      d_value = data[key]
      if shape_type_is_array:
        if not isinstance(d_value, list):
          return False
        for v in d_value:
          if not shape_type.validate(v):
            return False
      else:
        if not shape_type.validate(d_value):
          return False
    return True

  @staticmethod
  def shape(shape, data, initial_dict={}):
    result = initial_dict
    for key, value in shape.items():
      if key in data:
        result[key] = data[key]
    return result


def test_shaper():
  print("--pass--")
  print("Shaper.validate", Shaper.validate(
    {
      "a": "!boolean", 
      "b": "!string",
      "c": "!number",
      "d": "!null",
      "e": "boolean",
    }, 
    {
      "a": True,
      "b": "etc",
      "c": 123.1,
      "d": None,
    }
  ))
  print("Shaper.shape", Shaper.shape({"a": None}, {"a": True, "b": "etc"}))
  print("--fail--")
  print("Shaper.validate", Shaper.validate({"a": "boolean", "b": "number"}, {"a": True, "b": "etc"}))

def test_shaper_types():
  print("string_type.validate", string_type.validate("asd"))
  print("number_type.validate", number_type.validate(123))
  # print("Date?", shape_type_lookup["Date"].validate(datetime.now()))

def test():
  test_shaper_types()
  test_shaper()

# test()