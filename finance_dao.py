# -*- coding: utf-8 -*-
import requests
import json
from json import JSONDecodeError
import yfinance as yf
from datetime import datetime, date
from pandas_datareader import data
import logging

#logging.basicConfig(filename='finance_dao.log',format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s ',level=logging.INFO)


#### Clase que accede a datos del servidor Invertir Online
class Iol(object):
    status=200
    token = "0"
    refreshToken = "0"
    lista = []
    lista.append(('GGAL', 'GGAL.BA', 10, 0, 0,))
    lista.append(('YPF', 'YPFD.BA', 1, 0, 0))
    lista.append(('BMA', 'BMA.BA', 10, 0, 0))
    lista.append(('PAM', 'PAMP.BA', 25, 0, 0))
    lista.append(('BBAR', 'BBAR.BA', 3, 0, 0))
    lista.append(('CEPU', 'CEPU.BA', 10, 0, 0))
    lista.append(('CRESY', 'CRES.BA', 10, 0, 0))
    lista.append(('EDN', 'EDN.BA', 20, 0, 0))
    lista.append(('LOMA', 'LOMA.BA', 5, 0, 0))
    lista.append(('SUPV', 'SUPV.BA', 5, 0, 0))
    lista.append(('TEO', 'TECO2.BA', 5, 0, 0))
    lista.append(('TGS', 'TGSU2.BA', 5, 0, 0))
    lista.append(('TGS', 'TGSU2.BA', 5, 0, 0))

    def __init__(self):
        self.login()

    # Loguin almacena en una variable de clase el token de conexion.
    def login(self):
        #Loguin en Invertir Online
        usuario="martindonofri0"
        password="1982Tino"

        url="https://api.invertironline.com/token"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        payload = {'username': usuario, 'password': password, 'grant_type': 'password'}

        r = requests.post(url = url,headers=headers,data=payload)
        self.timestampLogin = datetime.now()
        self.status=r.status_code

        if (self.getStatus()!=200):
            raise ConnectionError("Fallo conexion IOL, CODE: "+str(r.status_code))
        body=json.loads(r.text)

        self.refreshToken = body["refresh_token"]
        self.token = body["access_token"]

    def getStatus(self):
        return self.status

    def getToken(self):
        ahora = datetime.now()
        diff = ahora - self.timestampLogin
        if diff.seconds > 600:
            logging.info("Haciendo refresh del token iol")
            url = "https://api.invertironline.com/token"
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            payload = {'refresh_token': self.refreshToken, 'grant_type': 'refresh_token'}
            r = requests.post(url=url, headers=headers, data=payload)
            body = json.loads(r.text)
            self.timestampLogin = datetime.now()
            self.refreshToken = body["refresh_token"]
            self.token = body["access_token"]
        logging.debug("getToken: "+self.token)
        return self.token

    def getCotiz(self, ticker, mercado='bCBA'):
        URL="https://api.invertironline.com/api/v2/"+mercado+"/Titulos/"+ticker+"/Cotizacion?mercado="+mercado+"&simbolo="+ticker+"&model.simbolo="+ticker+"&model.mercado="+mercado
        headers={'Authorization': "Bearer "+self.getToken()}
        r = requests.get(url = URL, headers = headers)
        #if r.status_code != 200:
            #raise ConnectionError("Fallo conexion IOL, CODE: " + str(r.status_code))
        body=""
        try:
            body=json.loads(r.text)
            listaPuntas=body['puntas']
        except (JSONDecodeError, KeyError):
            self.login()
            print('Fallo la consulta api iol, intento Reconexion. Status code: '+str(r.status_code))

        #print(' - - '+ticker+': '+json.dumps(body, indent=4, sort_keys=True))

        cantidadCompra = 0
        cantidadVenta = 0
        proporcionTicker = 0

        ##print(' - - '+ticker+': '+json.dumps(body, indent=4, sort_keys=True))

        for j in listaPuntas:
            cantidadCompra = cantidadCompra + float(j['cantidadCompra'])
            cantidadVenta = cantidadVenta + float(j['cantidadVenta'])

        if (float(cantidadCompra + cantidadVenta)!=0):
            proporcionTicker = (float(cantidadCompra) / float(cantidadCompra + cantidadVenta))


        return [float(body['cierreAnterior']),float(body['ultimoPrecio']), proporcionTicker]

    def getCotizConPuntas(self, ticker, mercado='bCBA'):
        URL = "https://api.invertironline.com/api/v2/" + mercado + "/Titulos/" + ticker + "/Cotizacion?mercado=" + mercado + "&simbolo=" + ticker + "&model.simbolo=" + ticker + "&model.mercado=" + mercado
        headers = {'Authorization': "Bearer " + self.token}

        r = requests.get(url=URL, headers=headers)
       # if r.status_code != 200:
       #     raise ConnectionError("Fallo conexion IOL, CODE: " + str(r.status_code))

        body = ""
        try:
            body = json.loads(r.text)
            listaPuntas = body['puntas']
        except (JSONDecodeError, KeyError):
            self.login()
            print('Fallo la consulta api iol, intento Reconexion. Status code: ' + str(r.status_code))

        # print(' - - '+ticker+': '+json.dumps(body, indent=4, sort_keys=True))

        cantidadCompra = 0
        cantidadVenta = 0
        precioCompra = 0
        precioVenta = 200000

        ##print(' - - '+ticker+': '+json.dumps(body, indent=4, sort_keys=True))
        for j in listaPuntas:
            if j['precioCompra']>precioCompra:
                precioCompra=j['precioCompra']
                cantidadCompra = j['cantidadCompra']
            if j['precioVenta']<precioVenta:
                precioVenta = j['precioVenta']
                cantidadVenta = j['cantidadVenta']


        return [float(body['cierreAnterior']), float(body['ultimoPrecio']), precioCompra, cantidadCompra, precioVenta, cantidadVenta]




    ## Devuelve un dataframe de Panda con las acciones del mercado BVBA y la cotiz del ultimo cierre
    # 'UltimoPrecio devuelve el precio actual de la accion

    def getCotizAccionesTodas(self):
        url = "https://api.invertironline.com/api/v2/Cotizaciones/Acciones/Merval/argentina"
        auth = "Bearer " + self.token
        headers = {'Authorization': auth}
        r = requests.get(url=url, headers=headers)
        body = json.loads(r.text)
        #print(json.dumps(body, indent=4, sort_keys=True))

        for titulo in body['titulos']:
            print("Ticker: "+titulo['simbolo']+" -- Ultimo Precio: $ {0:.2f}".format(titulo['ultimoPrecio'])+" Ultimo Cierre: $ {0:.2f}".format(titulo['ultimoCierre']))

    def getTitulos(self):
        url = "https://api.invertironline.com/api/v2/Cotizaciones/Acciones/Merval/argentina"
        auth = "Bearer " + self.token
        headers = {'Authorization': auth}
        r = requests.get(url=url, headers=headers)
        body = json.loads(r.text)
        #print(json.dumps(body, indent=4, sort_keys=True))
        result = []
        for titulo in body['titulos']:
            result.append(titulo['simbolo'])
        return result

    def getPropCompras(self, ticker, mercado='bCBA'):
        URL = "https://api.invertironline.com/api/v2/" + mercado + "/Titulos/" + ticker + "/Cotizacion?mercado=" + mercado + "&simbolo=" + ticker + "&model.simbolo=" + ticker + "&model.mercado=" + mercado
        auth = "Bearer " + self.token
        headers = {'Authorization': auth}
        r = requests.get(url=URL, headers=headers)
        body = json.loads(r.text)

        cantidadCompra = 0
        cantidadVenta = 0
        proporcionTicker = 0

        #print(' - - '+ticker+': '+json.dumps(body, indent=4, sort_keys=True))

        for j in body['puntas']:
            cantidadCompra = cantidadCompra + float(j['cantidadCompra'])
            cantidadVenta = cantidadVenta + float(j['cantidadVenta'])

        if (float(cantidadCompra + cantidadVenta) != 0):
            proporcionTicker = (float(cantidadCompra) / float(cantidadCompra + cantidadVenta))

        return proporcionTicker

    def comprar(self, ticker, cantidad, precio, validez):
        nrope = 0
        URL = "https://api.invertironline.com/api/v2/operar/Comprar"
        auth = "Bearer " + self.token

        headers = {'Authorization': auth}
        payload = {
            'mercado': 'bCBA',
            'simbolo': ticker,
            'cantidad': cantidad,
            'precio': precio,
            'plazo': 't2',
            'validez': validez
        }

        r = requests.post(url=URL, json=payload, headers=headers)

        if r.status_code > 299:
            raise ConnectionError("Fallo conexion IOL, CODE: " + str(r.status_code))
        
        return json.loads(r.text)

    def vender(self, ticker, cantidad, precio, validez):
        nrope = 0
        URL = "https://api.invertironline.com/api/v2/operar/Vender"
        auth = "Bearer " + self.token

        headers = {'Authorization': auth}
        payload = {
            'mercado': 'bCBA',
            'simbolo': ticker,
            'cantidad': cantidad,
            'precio': precio,
            'plazo': 't2',
            'validez': validez
        }

        r = requests.post(url=URL, json=payload, headers=headers)

        if r.status_code > 299:
            raise ConnectionError("Fallo conexion IOL, CODE: " + str(r.status_code))
        print(r.encoding)
        r.encoding = 'ISO-8859-1'
        return r.text

    def borrarOperacion(self, number):
        headers = {'Authorization': "Bearer " + self.token}
        r = requests.delete("https://api.invertironline.com/api/v2/operaciones/"+number, headers=headers)
        return r.text

    def getOperacion(self, number):
        headers = {'Authorization': "Bearer " + self.token}
        r = requests.get("https://api.invertironline.com/api/v2/operaciones/"+number, headers=headers)
        return r.text

    def getOperaciones(self):
        headers = {'Authorization': "Bearer " + self.token}
        r = requests.get("https://api.invertironline.com/api/v2/operaciones/", headers=headers)
        return json.loads(r.text)


### Clase que accede a datos del servidor Yahoo
class Yahoo(object):
    hoy=''
    def __init__(self):
        self.hoy = datetime.now().strftime('$Y-%m-%d')
    
    def getCotiz(self,ticker,mercado="bCBA"):
        cotiz=0
        serie = yf.download(ticker,period=self.hoy,interval='1m')
        if not (serie.empty):
            cotiz=float(serie.tail(1)['Close'])

        return float(cotiz)

### Clase que accede a datos del servidor Yahoo usando objeto PandaReader

class PandaDataReader(object):
    hoy=""

    def __init__(self):
        self.hoy = datetime.now().strftime('%Y-%m-%d')

    def getCotiz(self, ticker, mercado="bCBA"):
        cotiz = 0
        #start = datetime.datetime(2018, 1, 1)
        serie = data.get_data_yahoo(ticker, self.hoy)
        if not (serie.empty):
            cotiz = float(serie.tail(1)['Adj Close'])

        return float(cotiz)


##Test
#print('Prueba de valores de GGAL en todas las fuentes de datos.')
#y = Yahoo()
#iol = Iol()
#print(iol.getCotiz("BMA"))
#hoy=datetime.now().strftime('%Y-%m-%d')
#result1 = iol.comprar("BMA",1,232,hoy)
#print(result1)

#print(iol.vender("BMA",1,235,hoy))
#print(iol.borrarOperacion('23016794'))


#print(' GGAL YAHOO: '+ str(y.getCotiz('GGAL.BA')))
#print(' GGAL IOL: '+ str(iol.getCotiz('BMA')))
#print(' GGAL PandaDataReader: '+ str(pdr.getCotiz('GGAL.BA')))

#iol.getCotizAccionesTodas()

            

