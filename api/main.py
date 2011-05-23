#!/usr/bin/env python

# Copyright (c) 2009 Johan Uhle
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import util
from api import tracks
from api import locations
from api import check_location
from api.soundcloudconnect import main as scconnect_main
from api.soundcloudconnect import network
from api.soundcloudconnect import favorites

def main():
  application = webapp.WSGIApplication([(r'/api/tracks/([0-9]{1,64})', tracks.TrackIDHandler),
                                        ('/api/tracks.*', tracks.TracksHandler),
                                        ('/api/locations/maxtracks.*', locations.MaxTracksHandler),
                                        (r'/api/locations/([0-9]{1,64})', locations.LocationIDHandler),
                                        ('/api/soundcloud-connect/', scconnect_main.SoundCloudConnectHandler),
                                        ('/api/soundcloud-connect/followers/max/.*', network.MaxFollowersHandler),
                                        ('/api/soundcloud-connect/followings/max/.*', network.MaxFollowingsHandler),
                                        ('/api/soundcloud-connect/favorites/max/.*', favorites.MaxFavoritesHandler),                                        
                                        ('/api/soundcloud-connect/followers/tracks-in-location/.*', network.TracksInLocationFollowersHandler),
                                        ('/api/soundcloud-connect/followings/tracks-in-location/.*', network.TracksInLocationFollowingsHandler),                                        
                                        ('/api/soundcloud-connect/favorites/tracks-in-location/.*', favorites.TracksInLocationHandler),                                                                                
                                        ('/api/soundcloud-connect/followers/.*', network.LocationsFollowersHandler),
                                        ('/api/soundcloud-connect/followings/.*', network.LocationsFollowingsHandler),                                        
                                        ('/api/soundcloud-connect/favorites/.*', favorites.LocationsHandler),                                                                                
                                        ('/api/locations.*', locations.LocationsHandler),
                                        ('/api/check-location.*', check_location.CheckLocationHandler)], debug=util.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()