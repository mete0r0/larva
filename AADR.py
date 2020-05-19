# -*- coding: utf-8 -*-
import json
import logging
import pickle
import time
from datetime import datetime,date
import threading
import numpy
import yfinance as yf
from colorama import Fore

from finance_dao import Iol

logging.basicConfig(filename='larva.log',format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s ',level=logging.INFO)
#logging.basicConfig(format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s ')#,level=logging.INFO)


class AADR(object):
    lista=[] ##Lista que mantiene cotizaciónes al cierre anterior
    ## ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO) 
    compras=[] ##  ( TICKER, VALOR, CANTIDAD, NROOPERACION, VALORVENTAMIN, TIMESTAMP)
    ventas=[] ##   ( TICKER, VALOR, CANTIDADm NROOPERACION, TIMESTAMP)
    timeRefresh=10
    MONTOCOMPRA=1000
    GANANCIAPORCENTUAL = 1 #Constante que defije objetivo de ganancia relativa porcentual
    DIFPORCENTUALMINCOMPRA = GANANCIAPORCENTUAL+1 #Minima diferencia con el valor arbitrado par considerarlo en la compra.

    def __init__(self,lista):
        self.lista=lista
        self.lista.append(('GGAL','GGAL.BA',10,0,0,0))
        self.lista.append(('YPF','YPFD.BA',1,0,0,0))
        self.lista.append(('BMA','BMA.BA',10,0,0,0))
        self.lista.append(('PAM','PAMP.BA',25,0,0,0))
        self.lista.append(('BBAR','BBAR.BA',3,0,0,0))
        self.lista.append(('CEPU','CEPU.BA',10,0,0,0))
        self.lista.append(('CRESY','CRES.BA',10,0,0,0))
        self.lista.append(('EDN','EDN.BA',20,0,0,0))
        self.lista.append(('LOMA','LOMA.BA',5,0,0,0))
        self.lista.append(('SUPV','SUPV.BA',5,0,0,0))
        self.lista.append(('TEO','TECO2.BA',5,0,0,0))
        self.lista.append(('TGS','TGSU2.BA',5,0,0,0))

        self.hoy=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        print("Fecha: "+self.hoy)
        logging.info("INICIANDO LARVA "+self.hoy)

        self.lista.sort()
        self.cargar_cotiz()
        self.dolar_ccl_promedio=(self.calculo_ccl_AlCierreARG("GGAL.BA")+self.calculo_ccl_AlCierreARG("YPFD.BA")+self.calculo_ccl_AlCierreARG("BMA.BA")+self.calculo_ccl_AlCierreARG("PAMP.BA"))/4

        print("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))

        logging.info("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))
        self.cargar_ValoresArbitrados()
        self.setTimeRefresh(60)

        ##Cargo compras desde archivo
        with open("compras.dat", "rb") as f:
                self.compras = pickle.load(f)
        print("Cantidad compras en Inicio: "+str(len(self.compras)))
        print(self.compras)

        ##Cargo ventas desde archivo
        with open("ventas.dat", "rb") as f:
                self.ventas = pickle.load(f)
        print("Cantidad ventas en Inicio: "+str(len(self.ventas)))
        print(self.ventas)

    ##
    # Metodo que te carga el valor arbitrado de todos los tickers en la lista.
    def cargar_ValoresArbitrados(self):
        logging.info("Calculando CCL al cierre anterior")
        lista_aux=[]
        for campo in self.lista:
            valor_arbitrado = float(self.calculo_valor_arbitrado(campo[1],self.dolar_ccl_promedio))
            campo_aux=(campo[0], campo[1], campo[2], campo[3], campo[4], valor_arbitrado)
            lista_aux.append(campo_aux)
        self.lista=lista_aux


    ## Carga cotizaciones del cierre anterior en lista.
    def cargar_cotiz(self):
        logging.info('cargar_cotiz: Cargando cotizaciones ultimo cierre.')
        lista_aux=[]
        ultimoCierre=""
        for campo in self.lista:
            local_ca = 0
            adr_ca = 0
            try:
                hoy_aux=date.today()
                pd_local_aux = yf.download(campo[1], period="2d", interval="1d")
                pd_local = pd_local_aux.drop(hoy_aux).tail(1)
            except KeyError:
                logging.debug("CARGA COTIZ: No se pudo borrar el dia de hoy. "+ campo[1])
                pd_local = pd_local_aux.tail(1)

            if  not pd_local.empty:
                local_ca = pd_local['Close'].values[0]
                np_date = pd_local.index.values[0]
                ultimoCierre = numpy.datetime_as_string(np_date, "D")

                ##Con esta linea me traigo el ADR del mismo dia del local
                pd_adr = yf.download(campo[0], start=numpy.datetime_as_string(np_date, "D"), interval="1d").head(1)

                ## Con esta me traigo el ultimo ADR ##TODO
                #pd_adr = yf.download(campo[0], period="2d", interval="1d").tail(1)
                #print(pd_adr)

                if not pd_adr.empty:
                    adr_ca = pd_adr['Close'].values[0]
            logging.info(ultimoCierre+ " - "+campo[0] + " C. ADR ULT CIERRE {0:.2f}".format(adr_ca) + " C. Loc ULT CIERRE {0:.2f}".format(local_ca))

            campo_aux=(campo[0], campo[1], campo[2], adr_ca, local_ca, 0)
            lista_aux.append(campo_aux)
        self.lista=lista_aux

    def calculo_ccl(self, tickerlocal):
        cotizadrf=0
        cotizlocalf=0
        factor=0
        for campo in self.lista:
            if (campo[1] == tickerlocal):
                cotizadrf=campo[3]
                cotizlocalf=campo[4]
                factor=campo[2]
                break

        resultado = (float(cotizlocalf)/(float(cotizadrf)/float(factor)))
        #print (' ticket local: '+tickerlocal+ ' Cotiz ADR: '+ str(cotizadrf)+ ' Cotiz Local: '+str(cotizlocalf)+' Factor: '+str(factor)+' CCL: '+ str(resultado))
        return resultado

    ### Metodo que calcula es CCL al ultimo cierre.
    ##
    def calculo_ccl_AlCierreARG(self, tickerlocal):
        cotizadrf = 0
        cotizlocalf = 0
        factor = 1
        for campo in self.lista:
            if (campo[1] == tickerlocal):
                factor = campo[2]
                cotizlocalf = campo[4]
                cotizadrf = campo[3]
                break

        resultado = (float(cotizlocalf) / (float(cotizadrf) / float(factor)))
        logging.info(tickerlocal + " C. ADR: {0:.2f}".format(cotizadrf) + " C. Loc: {0:.2f}".format(cotizlocalf) + ' Fac.: ' + str(factor) + " CCL: {0:.2f}".format(resultado))
        return resultado

    def calculo_valor_arbitrado(self, tickerlocal, dolar_ccl_promedio):
        cotizadrf=0
        factor=0
        for campo in self.lista:
            if (campo[1] == tickerlocal):
                cotizadrf=campo[3]
                factor=campo[2]
                break
        
        return (cotizadrf/float(factor))*float(dolar_ccl_promedio)

    def imprimir_resultado(self, tickerlocal, valor_arbi):
        cotizadrf=0
        cotizlocalf=0
        for campo in self.lista:
            if (campo[1] == tickerlocal):
                cotizadrf=campo[3]
                cotizlocalf=campo[4]
                break
        diferencia = float(valor_arbi)-float(cotizlocalf)
        variacion = float((diferencia)*100)/float(cotizlocalf)
        print("TICKER: "+tickerlocal+"\t\t C LOCAL: {0:.3f}".format(cotizlocalf)+"\t C ADR: {0:.3f}".format(cotizadrf)+"\t C ARBI: {0:.3f}".format(valor_arbi)+"\t DIF: {0:.3f}".format(float(diferencia))+"\t VAR: {0:.3f}%".format(variacion))
        return 0


    def normalizar(self, valor, min, max):
        return (valor / (abs(max) + abs(min))) * 20



    ## Metodo que permite hacer seguimietno ONLINE de ARB.
    def larva(self):
        logging.info("Arranca larva: ")
        #vendedora = threading.Thread(target=self.worker_venta(), name='WorkerVenta')
        #vendedora.start()

        iol = Iol()

        ###
        ###
        ### Bucle principal
        while (True):
            ahora=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            print("Fecha: "+ahora)
            for tt in self.lista:
                tickerlocal = tt[1].split(".")[0]
                local_ca, local_up, precioCompra, cantidadCompra, punta_precioVenta, punta_cantidadVenta = iol.getCotizConPuntas(tickerlocal, mercado="BCBA")
                adr_ca, adr_up, adr_prop = iol.getCotiz(ticker=tt[0], mercado="NYSE")
                valor_arbi = float(tt[5])
                cotizlocalf = float(local_up)
                cotizadrf = float(adr_up)

                diferencia = float(valor_arbi)-float(cotizlocalf)
                variacion = float((diferencia)*100)/float(cotizlocalf)
                if (variacion>=self.DIFPORCENTUALMINCOMPRA):
                    print(Fore.BLUE+tickerlocal+"\t\t C LOCAL ACTUAL {0:.2f}".format(cotizlocalf)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion)+Fore.RESET)
                    ##################
                    ### Proceso Compra
                    valorCompraMax, valorVentaMin = self.calculoValoresCompraYVenta(cotizlocalf, valor_arbi)

                    if valorCompraMax != 0 and punta_precioVenta != 0 and valorCompraMax >= punta_precioVenta:
                        cantidad = self.MONTOCOMPRA // cotizlocalf
                        print(Fore.GREEN + " AVISO: Comprar: {0:.2f}".format(cantidad)+ " - Punta vendedora - Cant: {0:.2f}".format(
                            punta_cantidadVenta) + ", valor: {0:.2f}".format(punta_precioVenta) + Fore.RESET)
                        self.compra(tickerlocal, cotizlocalf, cantidad, valorVentaMin)
                else:
                    print(tickerlocal + "\t\t C LOCAL ACTUAL {0:.2f}".format(
                    cotizlocalf) + "\t\t C ADR ACTUAL: {0:.2f}".format(
                    cotizadrf) + "\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi) + "\t\t DIF: {0:.2f}".format(
                    float(diferencia)) + "\t\t VAR: {0:.2f}%".format(variacion))

                ## Proceso de venta
                if (len(self.compras) == 0):
                    logging.info("NO HAY COMPRAS HECHAS")
                else:
                    logging.info("Compras hechas: {0:.2f}".format(len(self.compras)))
                    self.xventa(iol,tickerlocal)


                logging.info(tickerlocal+"\t\t C LOCAL ACTUAL {0:.2f}".format(cotizlocalf)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion))
                                        
            ## TIEMPO DEL CICLO
            print("\n ... En Ejecucion..."+datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            time.sleep(1)

    def getTimeRefresh(self):
        return self.timeRefresh

    def setTimeRefresh(self,valor):
        self.timeRefresh=valor

    ## Metodo que implementa el Hilo de Venta
    def worker_venta(self):
        ## Proceso de VENTA
        ## Recorre lista de compras
        iol = Iol()
        print("inicio worker venta")
        while (True):
            if (len(self.compras) == 0):
                logging.info("NO HAY COMPRAS HECHAS")
            else:
                logging.info("Compras hechas: {0:.2f}".format(len(self.compras)))
                self.xventa(iol)
            time.sleep(2)

    def xventa(self, iol, ticker):
        logging.info("Reviso todos as compras y miro si alcanzo el valorVentaMin")
        for campo in self.compras:
            if ticker == campo[0]:
                loc_ca, loc_up, prop=iol.getCotiz(campo[0])
                valorMinVenta = campo[4]
                logging.info("Ticker: "+campo[0]+" Precio Actual: {0:.2f}".format(loc_up)+" Objetivo: {0:.2f}".format(valorMinVenta))
                if loc_up >= valorMinVenta:
                    print(Fore.BLUE+"\tObjetivo Venta CUMPLIDO: "+campo[0]+" Valor: {0:.2f}".format(loc_up)+Fore.RESET)
                    logging.info("\tObjetivo Venta CUMPLIDO: "+campo[0]+" Valor: {0:.2f}".format(loc_up))
                    self.vender(campo[0], loc_up, campo[2])

    ## Orden que envia a Vender a IOL y agrega a la lista de operaciones pendientes.
    # TODO Falta ver puntos y vender en funcion de eso.
    def vender(self, ticker, valor, cantidad):
        logging.info("Envio orden de VENTA A IOL: " + ticker + " Cantidad: {0:.2f}".format(
            cantidad) + " Valor: {0:.2f}".format(valor))
        if not self.buscar(self.ventas, ticker, valor, cantidad):
            self.agregarVenta(ticker, valor, cantidad)
            print(Fore.GREEN + "\tVenta Finalizada: " + ticker + " Valor: {0:.2f}".format(valor)+ " Cantidad: {0:.2f}".format(cantidad) + Fore.RESET)
        else:
            print("Venta ya hecha")
            logging.info("Esta venta ya fue hecha.")
        return 0

    ## Calcula el punto medio entre el valor y el arbitrado y se mueve 0,5 para cada lado
    def calculoValoresCompraYVenta(self, valor, valorArbitrado):

        medio = (valorArbitrado + valor) / 2
        valorCompraMax = medio - (medio * (self.GANANCIAPORCENTUAL/2) / 100)
        valorVentaMin = medio + (medio * (self.GANANCIAPORCENTUAL/2) / 100)

        logging.info("\tValor compra Maximo {0:.2f}".format(valorCompraMax))
        logging.info("\tValor venta Minimo {0:.2f}".format(valorVentaMin))

        return [valorCompraMax, valorVentaMin]


    ## Orden que envia a comprar a IOL y agrega a la lista de operaciones pendientes.
    def compra(self, ticker, valor, cantidad, valorVentaMin):
        logging.info("Envio orden de COMPRA A IOL: "+ticker+" Cantidad: {0:.2f}".format(cantidad)+" Valor: {0:.2f}".format(valor))

        costoTotal = (valor * 0.5 / 100) * 1.21
        valorTotal = valor + costoTotal
        logging.info("Costo total compra (0.5% + IVA): {0:.2f}".format(valorTotal))

        if not self.buscar(self.compras,ticker,valor,cantidad):
            self.agregarCompra(ticker, valor, cantidad, valorVentaMin)
            print("Comprado.")
        else:
            print("\tComprado anteriormente.")
            logging.info("Comprado anteriormente.")
        return 0
    


    ## Busqueda generica
    def buscar(self,lista,ticker,valor,cantidad):
        for tt in lista:
            if (tt[0] == ticker and tt[1] == valor and tt[2] == cantidad): return True

        return False

    ## Calcula la cantidad a comprar.
    def calculoCantidad(self, ticker, precio):
        if precio==0: return 0
        return self.MONTOCOMPRA // precio

    ## Imprime el listado de compras hechas
    def printCompras(self):
        print(self.compras)

    def leerArchCompras(self):
        fp = open('compras.json', 'r')
        ret = json.load(fp)
        fp.close()

    def agregarCompra(self, ticker, valor, cantidad, valorVentaMin):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.compras.append((ticker, valor, cantidad, "000", valorVentaMin, ahora))
        with open("compras.dat", "wb") as f:
            pickle.dump(self.compras, f)
    
    def borrarCompras(self):
        l = []
        self.compras = l
        with open("compras.dat", "wb") as f:
            pickle.dump(self.compras, f)
   

    def agregarVenta(self, ticker, valor, cantidad):
        logging.info("Agregando Venta Nueva")
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ventas.append((ticker, valor, cantidad, "000", ahora))
        with open("ventas.dat", "wb") as f:
            pickle.dump(self.ventas, f)

lista=[]
a = AADR(lista)
#a.larva()

#a.xcompra("BBAR",139, 100, 100, 232)
#a.xcompra("BBAR",250, 240, 100, 232)
#a.printCompras()
#a.agregarVenta("BMA", 24,1)
a.larva()

#y = Yahoo()
#iol = Iol()

#print(' GGAL YAHOO: '+ str(y.getCotiz('GGAL.BA')))
#print(' GGAL IOL: '+ str(iol.getCotiz('GGAL')))

#dolar_ccl_promedio=(aa.calculo_ccl_AlCierreARG("GGAL.BA")+aa.calculo_ccl_AlCierreARG("YPFD.BA")+aa.calculo_ccl_AlCierreARG("BMA.BA")+aa.calculo_ccl_AlCierreARG("PAMP.BA"))/4
#print("*****Dolar CCL (GGAL, YPFD, BMA, PAMP) Promedio: "+str(dolar_ccl_promedio))

#for tt in aa.lista:
#    valor_arbi = aa.calculo_valor_arbitrado(tt[1],dolar_ccl_promedio)
#    aa.imprimir_resultado(tt[1],valor_arbi)
