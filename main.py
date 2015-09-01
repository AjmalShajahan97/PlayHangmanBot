#Main do forca_bot 2.0
#-*- coding: utf-8 -*-

#Standard imports
import json
import logging
import random
import urllib
import urllib2

#app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

#Importa o BD
import bds

#TOKEN do bot no telegram
TOKEN = '105794279:AAEZQkZX-HnXHMBG8NHkc0CWyDjvpOnHM-U'

#URL base para funcionamento do sistema de Webhook
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

#Versão atual
VERSION = '2.a'

#Nossos IDs
creators = ['112228809', '112255461']

#Línguas suportadas
linguas = ['português(br)', 'english(us)']
# ==================================================

#Recebe os dados que serão repondidos e transforma em um dict
def toDict(chat_id, text, replyTo = None, replyMarkup = None):
    return dict(chat_id = chat_id, text = text, reply_to_message_id = replyTo, reply_markup = replyMarkup)

#Recebe uma matriz e a tranforma em um teclado personalizado
def makeKb(kb, resize_keyboard = None, one_time_keyboard = None, selective = None):
    resize_keyboard = resize_keyboard if resize_keyboard else False
    one_time_keyboard = one_time_keyboard if one_time_keyboard else False
    selective = selective if selective else False
    return json.dumps({'keyboard':kb, 'resize_keyboard':resize_keyboard, 'one_time_keyboard':one_time_keyboard, 'selective':selective})

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

        #Função que verifica se o forca_bot foi excluido ou se ele existe no BD
        def verifyBot(left_chat_participant = None, new_chat_participant = None, group_chat_created = None):
            if left_chat_participant:
                first_name = left_chat_participant['first_name'].encode('utf-8')
                if first_name == 'ccuemBot':
                    bds.delChat(chat_id)
                    return
            if new_chat_participant:
                first_name = new_chat_participant['first_name'].encode('utf-8')
                if first_name == 'ccuemBot':
                    bds.checkChat(chat_id)
                    return
            if group_chat_created:
                bds.checkChat(chat_id)
                return
            return

        #Dados que recebemos do telegram
        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        left_chat_participant = message.get('left_chat_participant')
        new_chat_participant = message.get('new_chat_participant')
        group_chat_created = message.get('group_chat_created')
        date = message.get('date')
        text = message.get('text').encode('utf-8').lower() if message.get('text') else message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = str(chat['id'])
        user_id = message['from']
        u_id = str(user_id.get('id')).encode('utf-8')
        u_name = user_id.get('first_name')

        #'Chama' a verificação
        if new_chat_participant:
            verifyBot(new_chat_participant = new_chat_participant)
        if left_chat_participant:
            verifyBot(left_chat_participant = left_chat_participant)
        if group_chat_created:
            verifyBot(group_chat_created = True)
        if not text:
            logging.info('no text')
            return

        #Função que envia o dict para o Telegram
        def reply(dict = None):
            if dict:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode(dict)).read()
            else:
                logging.error('no msg or img specified')
                resp = None
            logging.info('send response:')
            logging.info(resp)

        #Lê as configurações
        def getLanguage(chat_id):
            s = bds.getSettings(chat_id) #Classe settings
            if s.language == 'ptBR':
                import ptBR as l
                return l
            elif s.language == 'enUS':
                import enUS as l
                return l
            return

        def inicial_kb():
            l = getLanguage(chat_id)
            return [[l.ligar, l.desligar],[l.ajuda, l.rank], [l.config]] #possíveis keyboards

        #Funções que são executadas dependendo do comando recebido

        def start(chat_id):
            l = getLanguage(chat_id)
            if bds.getEnabled(chat_id):
                return toDict(chat_id, l.is_enabled)
            bds.setEnabled(chat_id, True)
            bds.checkChat(chat_id)
            l = getLanguage(chat_id)
            return toDict(chat_id, l.start_text, replyMarkup = makeKb(inicial_kb(), one_time_keyboard=True))

        def stop(chat_id):
            l = getLanguage(chat_id)
            bds.setEnabled(chat_id, False)
            return toDict(chat_id, l.stop_text)

        def ajuda(chat_id):
            l = getLanguage(chat_id)
            #Vai enviar ajuda dependendo do estado de jogo
            return toDict(chat_id, l.start_help_text)

        def config(chat_id):
            l = getLanguage(chat_id)
            language_kb = [['Português(BR)', 'English(US)']]
            bds.setWaiting(chat_id, True)
            keyboard = makeKb(language_kb, one_time_keyboard = True)
            return toDict(chat_id, l.linguas, replyMarkup = keyboard)

        def changeLanguage(chat_id, lingua):
            if 'português(br)' in lingua:
                bds.setLanguage(chat_id, 'ptBR')
                bds.setWaiting(chat_id, False)
                l = getLanguage(chat_id)
                keyboard = makeKb(inicial_kb(), one_time_keyboard=True)
                return toDict(chat_id, l.mudar_lingua, replyMarkup = keyboard)
            elif 'english(us)' in text:
                bds.setLanguage(chat_id, 'enUS')
                bds.setWaiting(chat_id, False)
                l = getLanguage(chat_id)
                keyboard = makeKb(inicial_kb(), one_time_keyboard=True)
                return toDict(chat_id, l.mudar_lingua, replyMarkup = keyboard)


        #Aqui começa a lógica principal
        s = bds.getSettings(chat_id)
        l = getLanguage(chat_id)

        text = '/start' if (text == l.ligar.lower()) else text #Tratamento para o caso do /start

        if not s.waiting:
            if '/start' in text:
                reply(start(chat_id))
            elif bds.getEnabled(chat_id):
                if l.desligar.lower() in text:
                    reply(stop(chat_id))
                elif l.ajuda.lower() in text:
                    reply(ajuda(chat_id))
                elif l.rank.lower() in text:
                    reply(toDict(chat_id, 'Sem rank'))
                elif l.config.lower() in text:
                    reply(config(chat_id))
                elif '/adm' in text:
                    if u_id in creators:
                        reply(toDict(chat_id, 'vai mandar msg pra todos'))
        else:
            if text in linguas:
                reply(changeLanguage(chat_id, text))

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
