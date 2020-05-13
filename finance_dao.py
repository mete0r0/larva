# -*- coding: utf-8 -*-
import requests
import json
from json import JSONDecodeError
import yfinance as yf
from datetime import datetime
from pandas_datareader import data


### Clase que accede a datos del servidor Invertir Online
class Iol(object):
    status=200
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


    token="0"
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
        self.status=r.status_code

        if (self.getStatus()!=200):
            raise ConnectionError("Fallo conexion IOL, CODE: "+str(r.status_code))
        #print("C IOL: "+ str(r.status_code))
        body=json.loads(r.text)
        self.token = body["access_token"]

    def getStatus(self):
        return self.status

    def getCotiz(self, ticker, mercado='bCBA'):
        URL="https://api.invertironline.com/api/v2/"+mercado+"/Titulos/"+ticker+"/Cotizacion?mercado="+mercado+"&simbolo="+ticker+"&model.simbolo="+ticker+"&model.mercado="+mercado
        auth="Bearer "+self.token
        headers={'Authorization': auth}

        r = requests.get(url = URL, headers = headers)
        if (r.status_code != 200):
            raise ConnectionError("Fallo conexion IOL, CODE: " + str(r.status_code))

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
#pdr = PandaDataReader()


#print(' GGAL YAHOO: '+ str(y.getCotiz('GGAL.BA')))
#print(' GGAL IOL: '+ str(iol.getCotiz('BMA')))
#print(' GGAL PandaDataReader: '+ str(pdr.getCotiz('GGAL.BA')))

#iol.getCotizAccionesTodas()

            

