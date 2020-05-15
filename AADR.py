# -*- coding: utf-8 -*-
from datetime import datetime,date
from finance_dao import Iol
from finance_dao import Yahoo
import yfinance as yf
import numpy
import logging
import time
from colorama import init, Fore, Back
#logging.basicConfig(filename='larva_debug.log',format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s ',level=logging.DEBUG)

logging.basicConfig(filename='larva.log',format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s ',level=logging.INFO)

class AADR(object):
    lista=[] ##Lista que mantiene cotizaciónes al cierre anterior
    compras=[] ##  ( TICKER, CANTIDAD, VALOR, NROOPERACION, TIMESTAMPi
    ventas=[]
    timeRefresh=60

    MONTOCOMPRA=1000
    ## ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO) 
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
        logging.info("INICIANDO LARVA"+self.hoy)

        self.lista.sort()
        self.cargar_cotiz()
        self.dolar_ccl_promedio=(self.calculo_ccl_AlCierreARG("GGAL.BA")+self.calculo_ccl_AlCierreARG("YPFD.BA")+self.calculo_ccl_AlCierreARG("BMA.BA")+self.calculo_ccl_AlCierreARG("PAMP.BA"))/4

        print("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))

        self.cargar_ValoresArbitrados()
        self.setTimeRefresh(60)

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
        iol = Iol()

        while (True):
            ahora=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            print("Fecha: "+ahora)
            for tt in self.lista:
                tickerlocal = tt[1].split(".")[0]
                local_ca, local_up, precioCompra, cantidadCompra, precioVenta, cantidadVenta = iol.getCotizConPuntas(tickerlocal, mercado="BCBA")
                adr_ca, adr_up, adr_prop = iol.getCotiz(ticker=tt[0], mercado="NYSE")
                valor_arbi = float(tt[5])
                cotizlocalf = float(local_up)
                cotizadrf = float(adr_up)

                diferencia = float(valor_arbi)-float(cotizlocalf)
                variacion = float((diferencia)*100)/float(cotizlocalf)
                if (variacion>=2): 
                    print(Fore.GREEN+tickerlocal+"\t\t C LOCAL ACTUAL {0:.2f}".format(cotizlocalf)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion)+Fore.RESET)
                    ###
                    result_compra, valorVentaMin=self.xcompra(tickerlocal,cotizlocalf, valor_arbi, punta_cantidadVenta, punta_precioVenta)

                    ##Proceso de venta

                    if (valorCompraMax!=0 and valorCompraMax> precioVenta):
                        print(Fore.BLUE+"Comprar punta, cantidad: {0:.2f}".format(cantidadVenta)+ " Valor: {0:.2f}".format(precioVenta)+Fore.RESET)

                else:
                    print(tickerlocal+"\t\t C LOCAL ACTUAL {0:.2f}".format(cotizlocalf)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion))
                logging.info(tickerlocal+"\t\t C LOCAL ACTUAL {0:.2f}".format(cotizlocalf)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion))
                                        
            ## TIEMPO DEL CICLO
            print("\n ... En Ejecucion")
            time.sleep(self.getTimeRefresh())

    def getTimeRefresh(self):
        return self.timeRefresh

    def setTimeRefresh(self,valor):
        self.timeRefresh=valor

    def xcompra(self,ticker, valor, valorArbitrado, punta_cantidadVenta, punta_precioVenta):
        logging.info("XCOMPRA - "+ticker+ " VALOR: {0:.2f}".format(valor)+ " VALOR ARBITRADO: {0:.2f}".format(valorArbitrado))
        valorCompraMax = 0
        ##Calculo costo compra con comision.
        costoTotal = (valor*0.5/100)*1.21
        valorTotal = valor + costoTotal
        logging.info("Costo total compra (0.5% + IVA): {0:.2f}".format(valorTotal))

        medio = (valorArbitrado + valor)/2
        valorCompraMax = medio - (medio*0.5/100)
        valorVentaMin = medio + (medio*0.5/100)
        
        logging.info("Valor compra Maximo {0:.2f}".format(valorCompraMax))
        logging.info("Valor venta Minimo {0:.2f}".format(valorVentaMin))
        resultado = self.compra(ticker,valor, 1, punta_cantidadVenta, punta_precioVenta)
        return [resultado, valorVentaMin]

    ## Orden que envia a comprar a IOL y agrega a la lista de operaciones pendientes.
    def compra(self, ticker, valor, cantidad, punta_cantidadVenta, punta_precioVenta):
        logging.info("Envio orden de COMPRA A IOL: "+ticker+" Cantidad: {0:.2f}".format(cantidad)+" Valor: {0:.2f}".format(valor))

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.compras.append((ticker, cantidad, valor, "000", ahora))

        return 0

        
        

lista=[]
aa = AADR(lista)
#aa.larva()
aa.xcompra("BMA",230, 240, 100, 232)

#y = Yahoo()
#iol = Iol()

#print(' GGAL YAHOO: '+ str(y.getCotiz('GGAL.BA')))
#print(' GGAL IOL: '+ str(iol.getCotiz('GGAL')))

#dolar_ccl_promedio=(aa.calculo_ccl_AlCierreARG("GGAL.BA")+aa.calculo_ccl_AlCierreARG("YPFD.BA")+aa.calculo_ccl_AlCierreARG("BMA.BA")+aa.calculo_ccl_AlCierreARG("PAMP.BA"))/4
#print("*****Dolar CCL (GGAL, YPFD, BMA, PAMP) Promedio: "+str(dolar_ccl_promedio))

#for tt in aa.lista:
#    valor_arbi = aa.calculo_valor_arbitrado(tt[1],dolar_ccl_promedio)
#    aa.imprimir_resultado(tt[1],valor_arbi)
