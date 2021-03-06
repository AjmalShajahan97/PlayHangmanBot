#-*- coding: utf-8 -*-
#Main do forca_bot 2.0

#Standard imports
import json
import logging
import random
import urllib
import urllib2
import time

#app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

#Imports nossos
import bds as bd
#import commands as c
#import preGame as p
#import game as g
import telegram as t
from tokens import *

#TOKEN do bot no telegram
TOKEN = test_tk

#URL base para funcionamento do sistema de Webhook
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

#Versão atual
VERSION = '2.1'

#Nossos IDs
creators = ['112228809', '112255461']

#Línguas suportadas
linguas = ['português(br)', 'english(us)', 'hebrew(il)']
# ==================================================

#Metodos que configuram a conexao do telegram com o App Engine
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        hangman = t.Hangman(body['message']) #Constrói o objeto principal
        #print(hangman)
        data = bd.configure(hangman) #Magia negra ou gambiarra? Fica ai a duvida

        shout = bd.getShout(data)
        if shout:
            bd.checkChatBd(shout[0])
            try:
                reply(c.toDict(shout[0], shout[1].encode('utf-8')))
            except Exception, e:
                logging.info((str(e) + ' = ' + shout[0].encode('utf-8')))
                if (str(e) == "HTTP Error 403: Forbidden"):
                    bds.delChat(shout[0])
                    bds.lessPos()
                    reply(c.toDict('-27626712', ('Chat ' + shout[0].encode('utf-8') + ' excluído')))
                else:
                    time.sleep(0.5)
                    try:
                        reply(c.toDict(shout[0], shout[1].encode('utf-8')))
                    except Exception, e:
                        print(e)






        #Função que envia o dict para o Telegram
        def reply(dict = None):
            if dict:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode(dict)).read()
            else:
                logging.error('no msg or img specified')
                resp = None
            logging.info('send response:')
            logging.info(resp)


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
