import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import re
from typing import Callable

class ParserToken:
  # pattern:
  processFn: Callable[[str], dict]
  name: str
  def __init__(self, name: str, pattern, processFn: Callable[[str, dict],str] = None):
    self.name = name
    self.pattern = pattern
    self.processFn = processFn

parser_tokens = [
  ParserToken("is_required", re.compile('(!|)'), lambda s, r: (s == '!')),
  ParserToken("type_name", re.compile('([a-z]|[A-Z])+'), lambda s, r: s),  
  ParserToken("is_array", re.compile('(\[\]|)'), lambda s, r: (s =='[]')), 
]

class LL1Parser:
  parser_tokens
  def __init__(self, parser_tokens: [ParserToken]):
    self.parser_tokens = parser_tokens

  def parse(self, string, result={}):
    results = []
    cur_index = 0
    for pt in self.parser_tokens:
      m = pt.pattern.match(string, cur_index)
      if m:
        start = m.start()
        end = m.end()
        got = m[0]
        if pt.processFn:
          result_tp = pt.processFn(got, result)
        else:
          result_tp = got
        print("--got", got)
        result[pt.name] = result_tp

        cur_index = end
      else:
        # no match
        return None
    return result

# schemaTypeNameParser = LL1Parser(parser_tokens)

def test_parser():
  schemaTypeNameParser = LL1Parser(parser_tokens)
  print(schemaTypeNameParser.parse('abc'))
  print(schemaTypeNameParser.parse('!abc[]'))