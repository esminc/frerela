import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

MAIN_PAGE_FOOTER_TEMPLATE = """    <form action="/sign?%s" method="post">
      <div><textarea name="content" rows="3" cols="60"></textarea></div>
      <div><input type="submit" value="Sign Guestbook"></div>
    </form>
    <hr>
    <form>Guestbook name:
      <input value="%s" name="guestbook_name">
      <input type="submit" value="switch">
    </form>
    <a href="%s">%s</a>
  </body>
</html>
"""

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)


class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Friend(ndb.Model):
    name = ndb.StringProperty(indexed=False)

class FriendDetail(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><body>')
        if not users.get_current_user():
            self.response.write('<a href="'+users.create_login_url(self.request.uri)+'">login</a></body></html>')
            return

        id = int(self.request.get('id'))
        friend = Friend.get_by_id(id)

        self.response.write('<div>%s</div>' % str(friend.name))
        self.response.write('</body></html>')

class FriendList(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><body>')
        if not users.get_current_user():
            self.response.write('<a href="'+users.create_login_url(self.request.uri)+'">login</a></body></html>')
            return

        # List friends
        self.response.write('<ul>')
        friends = Friend.query().fetch(10)
        for f in friends:
            key = str(f.key.id())
            self.response.write('<li><a href="/friend_detail?id=%s">%s</a></li>' % (key, f.name))
        self.response.write('</ul>')

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        sign_query_params = ''
        guestbook_name = ''
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE %
                            (sign_query_params, cgi.escape(guestbook_name),
                             url, url_linktext))
    def post(self):
        name = self.request.get('name')
        friend = Friend(name = name)
        friend.put()
        self.redirect('/')

class Guestbook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

class FriendRegister(webapp2.RequestHandler):
    def get(self):

        FRIEND_TEMPLATE = """    <form action="/" method="post">
              <input value="" name="name">
              <input type="submit" value="zuttomo">
            </form>
          </body>
        </html>
        """
        self.response.write(FRIEND_TEMPLATE)

app = webapp2.WSGIApplication([
    ('/', FriendList),
    ('/friend_register', FriendRegister),
    ('/friend_detail', FriendDetail),
    ('/sign', Guestbook),
], debug=True)
