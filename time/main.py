import time
import webapp2


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Current time wherever this google server is located: "+str(time.asctime( time.localtime(time.time()) )))


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
