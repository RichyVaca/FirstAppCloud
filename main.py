import webapp2

#3 metodo
import os
import jinja2
import random
import logging

from google.appengine.ext import ndb
from webapp2_extras import sessions
from Crypto.Hash import SHA256


intentos = 2
perdidas = 0
ganadas = 0
usuario = ""
psw = ""

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
template_values={}

def render_str(template,**params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()
    def render(self,template,**kw):
        self.response.out.write(render_str(template, **kw))
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

class Cuentas(ndb.Model):
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    win = ndb.StringProperty()
    lose = ndb.StringProperty()

class Login(Handler):
    def get(self):
        self.render("index.html")
    def post(self):
        global template_values
        usuario = self.request.get('username')
        psw = self.request.get('password')
        psw = SHA256.new(psw).hexdigest()

        logging.info('Checando usuario ='+str(usuario) + 'psw= ' + str(psw))
        msg = ''
        if psw == '' or usuario == '':
            msg = 'Please specify Account and Password'
            self.render("index.html", error = msg)
        else:
            consulta=Cuentas.query(ndb.AND(Cuentas.username==usuario, Cuentas.password==psw )).get()
            if consulta is not None:
                logging.info('POST consulta=' + str(consulta))

                self.session['username'] = consulta.username
                logging.info("%s just logged in" % usuario)
                template_values={
                    'username': self.session['username']
                }
                self.render("Bienvenida.html", user = template_values)
                
            else:
                logging.info('POST consulta=' + str(consulta))
                msg = 'Incorrect user or password.. please try again'
                self.render("index.html", error = msg)
        

class Registro(Handler):
    def get(self):
        self.render("registro.html")
    def post(self):
        usuario = self.request.get('username')
        psw = self.request.get('password')
        psw = SHA256.new(psw).hexdigest()

        cuenta = Cuentas(username = usuario, password = psw)

        cuentaKey = cuenta.put()

        cuenta_usuario = cuentaKey.get()

        if cuenta_usuario == cuenta:
            print "cuenta de usuario ", cuenta_usuario
            msg = "Gracias por registrarse"
            self.render("registro.html", error = msg)
        self.redirect("/")

class Logout(Handler):
    def get(self):
        if self.session.get('username'):
            msg = ''
            self.render("index.html", error = msg)
            del self.session['username']

class JugarPage(Handler):
    def get(self):
        self.render("juego1.html", intentos = intentos)
    def post(self):
        global intentos
        global ganadas 
        global perdidas 
        global usuario
        global psw
        if intentos > 0:
            opcion1 = self.request.get('opcionT')
            opcion1 = opcion1.lower()
            lista = ['piedra','tijera','papel']
            opcion2 = random.choice(lista)
            if opcion1 == opcion2:
                resultado = "Empate"
                intentos = intentos - 1
            elif (opcion1 == "piedra") and (opcion2 == "tijera"):
                resultado = "Piedra Gana Tijera, Ganaste..!"
                ganadas += 1
            elif (opcion2 == "piedra") and (opcion1 == "tijera"):
                resultado = "Piedra Gana Tijera, Perdiste. :("
                perdidas += 1
                intentos = intentos - 1
            elif (opcion1 == "piedra") and (opcion2 == "papel"):
                resultado = "Papel gana Piedra, Perdiste. :("
                perdidas += 1
                intentos = intentos - 1
            elif (opcion2 == "piedra") and (opcion1 == "papel"):
                resultado = "Papel gana piedra, Ganaste..!"
                ganadas += 1
            elif (opcion1 == "papel") and (opcion2 == "tijera"):
                resultado = "Tijera gana Papel, Perdiste. :("
                perdidas += 1
                intentos = intentos - 1
            elif (opcion2 == "papel") and (opcion1 == "tijera"):
                resultado = "Tijera gana Papel, Ganaste..!"
                ganadas += 1
            else:
                resultado = "opcion invalida"
            consulta = Cuentas.query(ndb.AND(Cuentas.username==usuario,
                        Cuentas.password==psw)).get()
            if ganadas > 0:
                if consulta is not None:
                    consulta.win = consulta.win + 1
                    consulta.put()
                    ganadas = 0
            if perdidas > 0:
                if consulta is not None:
                    consulta.lose = consulta.lose + 1
                    consulta.put()
                    perdidas = 0
            
            self.render('juego1.html', resultado = resultado, intentos = intentos+1)
        elif intentos == 0:
            self.render("index.html")
            intentos = 2

        
            
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'some-secret-key',
}


app = webapp2.WSGIApplication([('/', Login),
                               ('/click_login',Login),
                               ('/click_jugar',JugarPage),
                               ('/click_dale',JugarPage),
                               ('/click_salir',Logout),
                               ('/click_registro',Registro)

], debug=True, config=config)
        