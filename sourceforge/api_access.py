import urllib.request, urllib.error
import urllib.parse as parse
import oauth2 as oauth
import certifi

PROJECT='test'

CONSUMER_KEY=''
CONSUMER_SECRET=''

ACCESS_KEY=''
ACCESS_SECRET=''

URL_BASE='https://sourceforge.net/rest/'

consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
access_token = oauth.Token(ACCESS_KEY, ACCESS_SECRET)
client = oauth.Client(consumer, access_token)
client.ca_certs = certifi.where()

response = client.request(
    URL_BASE + 'p/has_access')
print("Done.  Response was:")
print(response[0]['status'])