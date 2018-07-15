# coding: utf-8
from google.appengine.ext import ndb
import webapp2
import json

def getAPIObject(id):
	obj = None
	try:
		obj = ndb.Key(urlsafe=id).get()
	except ProtocolBufferDecodeError:
		pass
	return obj
	
class Boat(ndb.Model):
  name = ndb.StringProperty(required=True)
  type = ndb.StringProperty(required=True)
  length = ndb.IntegerProperty(required=True)
  at_sea = ndb.BooleanProperty()

class Slip(ndb.Model):
  number = ndb.IntegerProperty(required=True)
  current_boat = ndb.StringProperty()
  arrival_date = ndb.StringProperty() 
  
class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write(
	'''This is the REST API Design and Implementation assignment for CS 496.
	
	This is a REST API with no front-end interaction. Please use HTTP commands to interact with the boats and slips.
	
	Reference:
		Boats:
		GET /boats   --   lists all boats
		GET /boats/{boat id}  --  lists all info about selected boat
		POST /boats  --  Creates a boat. Expects JSON data of a name (string), a type (string) and a length (int). Returns JSON data including boat's id. at_sea defaults to true, changed using the docking PUT.
		DELETE /boats/{boat id}  --  Deletes selected boat
		PATCH /boats/{boat id}  --  Edits selected boat. Expects JSON data in same form as POST, but some values can be excluded.

		Slips:
		GET /slips  --  lists all slips
		GET /slips/{slip id}  --  lists all info about selected slip
		POST /slips  --  Creates a slip. Expects JSON data of number (int). Numbers are unique. Defaults current_boat and arrival_date to null, changed using the docking PUT.
		DELETE /slips/{slip id}  --  Deletes selected slip, any docked ships set sail.
		PATCH /slips/{slip id}  --  Edits selected slip number. Expects JSON in same form as POST.

		Docking:
		PUT /slips/{slip id}/boat  --  Note that it is "boat" on the end, not "boats". Moves a boat into a slip. Expects JSON data containing the boat_id (string) and the arrival_data (string). Sets at_sea to false on boat.
''')

class BoatHandler(webapp2.RequestHandler):

  def __init__(self, *args, **kwargs):
    self.err = False
    super(BoatHandler, self).__init__(*args, **kwargs)

  def post(self):    
      body = json.loads(self.request.body)
      body['at_sea'] = True
      new_boat = Boat(**body)
      new_boat.put()
      boat_dict = new_boat.to_dict()
      boat_dict['id'] = new_boat.key.urlsafe()
      boat_dict['self'] = '/boats/' + new_boat.key.urlsafe()
      self.response.write(json.dumps(boat_dict))
 
  def patch(self, id=None):
    if id:
      boat = ndb.Key(urlsafe=id).get()
      if boat:
        boat_data = json.loads(self.request.body)
        if 'name' in boat_data:
          boat.name = boat_data['name']
        if 'type' in boat_data:
          boat.type = boat_data['type']
        if 'length' in boat_data:
          boat.length = boat_data['length']
        if 'at_sea' in boat_data:
          boat.at_sea = boat_data['at_sea']
          for slip in Slip.query(Slip.current_boat == id):
            if slip.current_boat and slip.arrival_date:
              slip.current_boat = ""
              slip.arrival_date = ""
              slip.put()
        boat.put()
        boat_dict = boat.to_dict()
        self.response.write(json.dumps(boat_dict))
      else:
        self.response.status = 405
        self.response.write("Error: Invalid boat id")
    else:
      self.response.status = 403
      self.response.write("Error: Invalid boat id")

  def get(self, id=None):
    if id:
      boat = ndb.Key(urlsafe=id).get()
      if boat:
        boat_dict= boat.to_dict()
        boat_dict['self'] = "/boats/" + id
        self.response.write(json.dumps(boat_dict))
      else:
        self.response.status = 405
        self.response.write("Error: Invalid boat id")
    else: 
        boats = Boat.query().fetch()
        boat_dicts = {'Boats':[]}
        for boat in boats:
          id = boat.key.urlsafe()
          boat_data = boat.to_dict()
          boat_data['self'] = '/boats/' + id
          boat_data['id'] = id
          boat_dicts['Boats'].append(boat_data)
        self.response.write(json.dumps(boat_dicts))

  def delete(self, id=None):
    if id:
      boat = ndb.Key(urlsafe=id).get()
      if boat:
        for slip in Slip.query(Slip.current_boat == id):
          if slip.current_boat:
            slip.current_boat = ""
          if slip.arrival_date:
            slip.arrival_date = ""
          slip.put()
        boat.key.delete()
        self.response.status = 200
        self.response.write("Boat deleted successfully")
      else:
        self.response.status = 405
        self.response.write("Error: Invalid boat id")


class SlipHandler(webapp2.RequestHandler):

  def __init__(self, *args, **kwargs):
    self.err = False
    super(SlipHandler, self).__init__(*args, **kwargs)

  def post(self, id=None):    
    try:
      body = json.loads(self.request.body)
    except:
      self.response.status = 405
      self.response.write("ERROR: Invalid JSON")
    if Slip.query(Slip.number == body['number']).get(): 
      self.response.status = 403
      self.response.write("Error: Invalid number, slip number already assigned.")
    if not self.err:
      body['current_boat'] = "null";
      new_slip = Slip(**body)
      new_slip.put()
      id = new_slip.key.urlsafe()
      slip_data = new_slip.to_dict()
      slip_data['id'] = id
      slip_data['self'] = '/slips/' + id
      if slip_data['current_boat'] != 'null':
        slip_data['boat_link'] = '/boats/' + slip_data['current_boat']
      self.response.write(json.dumps(slip_data))

  def get(self, id=None):
    if id:
      slip = ndb.Key(urlsafe=id).get()
      if slip:
        slip_dict = slip.to_dict()
        slip_dict['self'] = "/slips/" + id
        self.response.write(json.dumps(slip_dict))
      else:
        self.response.status = 405
        self.response.write("Error: Invalid slip id")
    else: 
        slips = Slip.query().fetch()
        slip_dicts = {'Slips':[]}
        for slip in slips:
          id = slip.key.urlsafe()
          slip_data = slip.to_dict()
          slip_data['self'] = '/slips/' + id
          slip_data['id'] = id
          slip_dicts['Slips'].append(slip_data)

        self.response.write(json.dumps(slip_dicts))

  def delete(self, id=None):
    if id:
      slip = ndb.Key(urlsafe=id).get()
      if slip:
        if slip.current_boat != "": 
          boats = Boat.query().fetch()
          for boat in boats:
            id = boat.key.urlsafe()
            if id == slip.current_boat:
              boat.at_sea = True
              boat.put()
        slip.key.delete()
        self.response.status = 200
        self.response.write("Slip deleted successfully")
      else:
        self.response.status = 405
        self.response.write("Error: Invalid slip id")
    else: 
        self.response.status = 403
        self.response.write("Error: Invalid slip id")

  def patch(self, id=None):
    if id:
      slip = ndb.Key(urlsafe=id).get()
      if slip:
        slip_data = json.loads(self.request.body)
        if 'number' in slip_data:
          if Slip.query(Slip.number == slip_data['number']).get(): 
            self.response.status = 403
            self.response.write("Error: Invalid number, slip number already assigned.")
          slip.number = slip_data['number']
        slip.put()
        slip_dict = slip.to_dict()
        self.response.write(json.dumps(slip_dict))
      else:
        self.response.status = 403
        self.response.write("ERROR: Invalid slip ID")
    else:
      self.response.status = 403
      self.response.write("ERROR: Boat id required for PATCH")

class DockHandler(webapp2.RequestHandler):
  def put(self, slip_id):
    self.err = False
    print(self.request.body)
    err = False
    try: 
      body = json.loads(self.request.body)
    except ValueError: 
      self.response.status = 405 
      self.response.write("ERROR: Invalid JSON")
      self.err = True
    if not self.err:
      boat = getAPIObject(body['boat_id'])
      if not boat:
        self.response.status = 405 
        self.response.write("ERROR: Invalid boat ID")
        self.err = True
    if not self.err:
      slip = getAPIObject(slip_id)
      if not slip:
        self.response.status = 405 
        self.response.write("ERROR: Invalid slip ID")
        self.err = True
    if not self.err:
      if slip.current_boat != 'null':
        self.response.status = 403 
        self.response.write("ERROR: Invalid slip, boat already docked")
        self.err = True
    if not self.err:
      slip.arrival_date = body['arrival_date']
      slip.current_boat = body['boat_id']
      boat.at_sea = False
      slip.put()
      boat.put()
      self.response.write(json.dumps(slip.to_dict()))

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH', 'PUT',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boats', BoatHandler),
    ('/boats/(.*)', BoatHandler),
    ('/slips', SlipHandler),
    ('/slips/(.*)/boat', DockHandler),
    ('/slips/(.*)', SlipHandler),
], debug=True)