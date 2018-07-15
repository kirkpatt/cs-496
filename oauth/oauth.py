from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import logging 
import webapp2
import json
import string
import random
import urllib

# Note that this will be very similar to my assignment from the last time I took this class. Dunno if you do an automated code checker or something, but this'll probably trigger it if you do.
# But, here I am citing myself for most of this code:
# Large parts of this program courtesy of Taylor Kirkpatrick

# This function courtesy http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

class OauthHandler(webapp2.RequestHandler):
  def get(self):
    code = self.request.get('code')
    statevar = self.request.get('state')
    if statevar == memcache.get('authState'):
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
    
      authHead = {}
      authHead['Authorization'] = 'Bearer ' + token
      result = urlfetch.fetch(url='https://www.googleapis.com/plus/v1/people/me', headers=authHead)
      data = json.loads(result.content)
      firstname = data["name"]["givenName"]
      lastname = data["name"]["familyName"]
      googleplus = data["url"]
      self.response.write("First name: " + firstname + "<br><br>Last name: " + lastname + "<br><br>Google+: <a href='" + googleplus + "'>" + googleplus + "</a><br><br>State variable: "+ statevar)
    

    

class Privacy(webapp2.RequestHandler):
  def get(self):
      self.response.write('This is a test implementation of OAuth, it will simply display back to you your Google+ profile information.<br><br>No data is intentionally kept. This project is for testing purposes only.')

class MainPage(webapp2.RequestHandler):
  def get(self):
    new_id = id_generator()
    memcache.delete(key='authState') # Clear it out just in case my site is super popular
    memcache.add(key="authState", value=new_id, time=120) # Remains for two minutes
    self.response.write('This is a test implementation of OAuth, it will simply display back to you your Google+ profile information.<br><br>')
    self.response.write('<a href="https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=966293361107-32as5ricq9g1gu30utfo13ahbbrd84hd.apps.googleusercontent.com&redirect_uri=https://auth-195701.appspot.com/oauth&scope=email&state=' + new_id + '">Click here to log in to your Google account</a><br><br>')
    self.response.write('<a href="https://auth-195701.appspot.com/privacy">Privacy Information</a>')
	
app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/privacy', Privacy),
  ('/oauth', OauthHandler)
], debug=True)