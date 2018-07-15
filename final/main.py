# coding: utf-8
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import webapp2
import json
import logging 
import string
import random
import urllib

def getAPIObject(id):
	obj = None
	try:
		obj = ndb.Key(urlsafe=id).get()
	except:
		pass
	return obj
    
def passAuth(self):
    body = json.loads(self.request.body)
    if 'token' in body:
        authHead = {}
        authHead['Authorization'] = 'Bearer ' + body['token']
        
        result = urlfetch.fetch(url='https://www.googleapis.com/plus/v1/people/me', headers=authHead)
        data = json.loads(result.content)
        passedAuth = data['isPlusUser']
        if (passedAuth == True):
            name = data['name']['givenName']
        else:
            name = False
        return name	
    else:
        self.response.status = 403
        self.response.write("Error: No token included in body. For non-GET requests, include a token in the json body.")
	
class OauthHandler(webapp2.RequestHandler):
  def get(self):
    code = self.request.get('code')
    # The following urlfetch portion was adapted from the answers on piazza post @186 (from the last class, probably not something you can view now. Kept for posterity)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload ={
    'code': code,
    'client_id': "966293361107-32as5ricq9g1gu30utfo13ahbbrd84hd.apps.googleusercontent.com",
    'client_secret': "DCLN4mIsSUmrA5HEycmhNP6m",
    'redirect_uri': "https://auth-195701.appspot.com/oauth",
    'grant_type': 'authorization_code'
    }
    result = urlfetch.fetch(
      url = "https://www.googleapis.com/oauth2/v4/token",
      payload=urllib.urlencode(payload),
      method=urlfetch.POST,
      headers=headers
    )
    data = json.loads(result.content)
    token = data["access_token"]
    
    self.response.write(token)
	
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
    self.response.write('<a href="https://auth-195701.appspot.com/privacy">Privacy Information</a> in the event Google overreacts like last year.<br><br>')
    self.response.write('A token is required to interact with the REST API. <a href="https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=966293361107-32as5ricq9g1gu30utfo13ahbbrd84hd.apps.googleusercontent.com&redirect_uri=https://auth-195701.appspot.com/oauth&scope=email&state=12345678">Click here to generate a token.</a><br><br>')
	

class Privacy(webapp2.RequestHandler):
  def get(self):
      self.response.write('This is a test implementation of OAuth and a REST API. No user\'s personal information is stored. This project is for testing purposes only.')

class BoatHandler(webapp2.RequestHandler):

  def __init__(self, *args, **kwargs):
    self.err = False
    super(BoatHandler, self).__init__(*args, **kwargs)

  def post(self):   
      name = passAuth(self)
      if name:
          self.response.write(name+" is authenticated for access.")
          body = json.loads(self.request.body)
          body.pop('token')
          body['at_sea'] = True
          new_boat = Boat(**body)
          new_boat.put()
          boat_dict = new_boat.to_dict()
          boat_dict['id'] = new_boat.key.urlsafe()
          boat_dict['self'] = '/boats/' + new_boat.key.urlsafe()
          self.response.write(json.dumps(boat_dict))        
 
  def patch(self, id=None):
    name = passAuth(self)
    if name:
        self.response.write(name+" is authenticated for access.")
        if id:
          boat = ndb.Key(urlsafe=id).get()
          if boat:
            boat_data = json.loads(self.request.body)
            boat_data.pop('token')
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
    name = passAuth(self)
    if name:
        self.response.write(name+" is authenticated for access.")
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
    name = passAuth(self)
    if name:
        self.response.write(name+" is authenticated for access.")
        try:
          body = json.loads(self.request.body)
          body.pop('token')
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
    name = passAuth(self)
    if name:
        self.response.write(name+" is authenticated for access.")
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
    name = passAuth(self)
    if name:
        self.response.write(name+" is authenticated for access.")
        if id:
          slip = ndb.Key(urlsafe=id).get()
          if slip:
            slip_data = json.loads(self.request.body)
            slip_data.pop('token')
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
    name = passAuth(self)
    if name:
        self.response.write(name+" is authenticated for access.")
        self.err = False
        print(self.request.body)
        err = False
        try: 
          body = json.loads(self.request.body)
          body.pop('token')
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
	('/privacy', Privacy),
	('/oauth', OauthHandler),
    ('/boats', BoatHandler),
    ('/boats/(.*)', BoatHandler),
    ('/slips', SlipHandler),
    ('/slips/(.*)/boat', DockHandler),
    ('/slips/(.*)', SlipHandler),
], debug=True)