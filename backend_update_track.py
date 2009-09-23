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

from google.appengine.runtime import DeadlineExceededError
from google.appengine.api import memcache
from google.appengine.ext import webapp 

import wsgiref.handlers                
import logging
import time
import os

import models
import backend_utils

	
class FetchTrackInfo(webapp.RequestHandler):
	def post(self):
		"""
		This script fetches the information for a track. It is meant to be called via TaskQueue.
		"""
     
		logging.info("Working the taskqueue. Fetching a new track.")
		
		try:                  
			# fetch track info from memcache
			track_id = self.request.get('track_id')       
			track = memcache.get(track_id, namespace="backend_update_track")
			if track is None:
				logging.error("Fetching memcache item %s failed in backend track update" % track_id)  
				self.error(500)
				return
					
			logging.info("Received the track \"%s\" by \"%s\" (id: %s, created at: %s)." % \
									(track['title'], track['user']['username'], track['id'], track['created_at']))
			
			# check if track is already in the datastore
			if models.Track.all().filter('ID', int(track['id'])).count() != 0: 
				logging.info("The track is already in the datastore.")
				return # return 200. task gets deleted from task queue

			# check if track meets our needs
			if not track['streamable'] or track['sharing'] != 'public':
				logging.info("The track does not match our needs. Will not be used.")
				if not memcache.delete(track_id, namespace="backend_update_track"):
					logging.error("Deletion from Memcache was not successfull.")
					self.error(500)
				return # return 200. task gets deleted from task queue
      
			# check if user is already in the datastore 		
			user = models.User.all().filter('ID', int(track['user_id'])).get()
			if user:
				logging.info("User is already in datastore as username: %s id: %i" % \
																																(user.username, user.id))
				track['user'] = user
			else:
 		 		# fetch complete user data
				logging.info("User is not in the datastore yet. Fetching user data.")
				track['user'] = backend_utils.open_remote_api("/users/%s.json" % \
																								track['user']['permalink'], "soundcloud") 
																								
				logging.info("User data fetched.")  
                    
 				# fetching location
		 		location = models.Location.all().filter('city', track['user']['city']).filter('country', track['user']['country']).get()
				if location:
						logging.info("Location is already in datastore: city: %s country: %s lat/lon: %s" % \
																																	 (track['user']['city'], track['user']['country'], "later"))
				else:

					try:                             
						logging.info("Location is not in the datastore yet. Fetching it ...")
						gecached_location = backend_utils.get_location(track['user']['city'], track['user']['country'])
	  
					 	location = models.Location( \
												location = gecached_location['location'],
												city = unicode(gecached_location['city']),
												country = unicode(gecached_location['country']),   
												track_counter = 1)
					
						logging.info("Location for User \"%s\" is %s / %s." % (track['user']['username'], location.location.lat, location.location.lon))
		
						location.put()
		                  
					except RuntimeError:
						logging.info("No Location for User \"%s\" with City/Country: \"%s / %s\"." % \
												(track['user']['username'], track['user']['city'], track['user']['country']))
		 				if not memcache.delete(track_id, namespace="backend_update_track"):
							logging.error("Deletion from Memcache was not successfull.") 
							self.error(500)
						return # return 200. task gets deleted from task queue
				
 				user = models.User( \
									ID = track['user']['id'],
									permalink = track['user']['permalink'],
									permalink_url = track['user']['permalink_url'],
									username = track['user']['username'],
									fullname = track['user']['full_name'],
									avatar_url = track['user']['avatar_url'],
									location = location.key())	         
				user.put()     

			backend_utils.write_track_to_cache(track, user)
				
			if not memcache.delete(track_id, namespace="backend_update_track"):
				logging.error("Deletion from Memcache was not successfull.")
	  		self.error(500)
			return # return 200. task gets deleted from task queue
								# tracks = backend_utils.remove_unusable_tracks(tracks)			
								# tracks = backend_utils.add_complete_user_data(tracks)
								# logging.info("Found %i new tracks" % len(tracks)) 
								# logging.info("Finished reading data from Soundcloud")
								# 
								# logging.info("Going to write %i new tracks to DB." % len(tracks)) 
								# counter_write = backend_utils.write_tracks_to_cache(tracks)
								# logging.info("Written %i new tracks to DB." % counter_write) 
								
	
		except DeadlineExceededError:
			logging.warning("Backend Update has been canceled due to Deadline Exceeded")
			for name in os.environ.keys():
				logging.info("%s = %s" % (name, os.environ[name]))		 
																																		 
def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/backend-update/track', FetchTrackInfo),
  ]))            
			
if __name__ == '__main__':
	main()