# -*- coding: utf-8 -*-
import logging
import logging.handlers
import time as ti
from datetime import datetime, timedelta, time
import threading
import numpy
import yfinance as yf
from colorama import Fore
import os
from finance_dao import Iol
import json
from routingorder import RoutingOrder, Estado
from dao import Dao

class AADR(object):
    lista = [] ##    ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO) ##Lista que mantiene cotizaciónes al cierre anterior ##
    compras = [] ##  ( TICKER, VALOR, CANTIDAD, NROOPERACION, Estado(Enum), TIMESTAMP, VALORVENTAMINVALORVENTAMIN)
    ventas = [] ##   ( TICKER, VALOR, CANTIDAD, NROOPERACION, Estado(Enum), TIMESTAMP)
    listaValoresActualesAcciones = [] ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    listaValoresActualesAdrs = [] ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    listaccl = [] ##Lista de historicos CCL.
    listaIndices = []

    fechaUltimoCierreLocal = ""
    fechaUltimoCierreAdr = ""
    TIMEREFRESH = 10 ## Valor por defecto. Toma el valor del archivo config.json
    #MONTOCOMPRA = 2000 # SOLO SE COMPRA de a 1 papel
    GANANCIAPORCENTUAL = 1 #Constante que defije objetivo de ganancia relativa porcentual
    DIFPORCENTUALMINCOMPRA = GANANCIAPORCENTUAL+0.4 #Minima diferencia con el valor arbitrado par considerarlo en la compra.
    PORCENTUALINDICES = 0.2 # Porcentaje de indice de otros mercados que tiene que superar para poder habilitar la compra.
    FECHALIMITECOMPRA11 = 15
    MINUTEGRADIENTEVENTA = 30
    PERIODOCOMPRA = FECHALIMITECOMPRA11 ## Periodo maximo de compra.
    PERIODOVENTAFORZADAMIN = 300 ## 16hs comienza el horario de venta a costo.
    enPeriodoCompra = False
    FINVENTAS = False
    #GANANCIA = float(0)

    MODOTEST = 0
    CONRUTEO = True
    horarioApertura = time(hour=11, minute=00, second=0)
    PORCENTUALINDICES = 0.2

    def __init__(self, lista, fecha):
        self.logger= self.loguear()
        self.logger.info("Iniciando Larva")

        self.fecha = fecha
        self.iol = Iol()
        self.getConfig()
        self.dao = Dao(self.PATH)

        ### Indices [TICKER YAHOO, Desc, Cotiz cierre anterior, Cotiz actual]
        self.listaIndices.append(['^GSPC',"S&P 500", 0, 0]) ## S&P 500
        #self.listaIndices.append(['^IXIC',"NASDAQ", 0, 0]) ## NASDAQ
        #self.listaIndices.append(['^N225', "Nikkei", 0, 0]) ## Nikkei
        #self.listaIndices.append(['^IBEX',"IBEX", 0, 0]) ## IBEX
        #self.listaIndices.append(['^GDAXI',"DAX-ALEMANIA", 0, 0]) ## DAX PERFORMANCE-INDEX
        #self.listaIndices.append(['^HSI',"HANG SENG INDEX", 0, 0]) ## HANG SENG INDEX

        self.getPrincipalesIndices(fecha)
        print("Lista de indices.")
        print(self.listaIndices)

        if (self.MODOTEST != 1):
            self.lista=lista
            self.lista.append(['GGAL','GGAL.BA',10,0,0,0])
            self.lista.append(['YPF','YPFD.BA',1,0,0,0])
            self.lista.append(['BMA','BMA.BA',10,0,0,0])
            self.lista.append(['PAM','PAMP.BA',25,0,0,0])
            self.lista.append(['BBAR','BBAR.BA',3,0,0,0])
            self.lista.append(['CEPU','CEPU.BA',10,0,0,0])
            self.lista.append(['CRESY','CRES.BA',10,0,0,0])
            self.lista.append(['EDN','EDN.BA',20,0,0,0])
            self.lista.append(['SUPV','SUPV.BA',5,0,0,0])
            self.lista.append(['TEO','TECO2.BA',5,0,0,0])
            self.lista.append(['TGS','TGSU2.BA',5,0,0,0])
            self.lista.sort()
            self.cargar_cotiz(fecha)

            ## Guardo la lista
            self.dao.save(self.lista, "lista", self.fecha)
            ## Guardo la listaValoresActualesAcciones
            self.dao.save(self.listaValoresActualesAcciones,"listaValoresActualesAcciones", self.fecha)
        else: # MODO TEST
            self.dao.load(self.lista,"lista",self.fecha)
            print("Cantidad lista en Inicio: " + str(len(self.lista)))
            print(self.lista)
            ##Cargo listaValoresActualesAcciones desde archivo
            self.dao.load(self.listaValoresActualesAcciones, "listaValoresActualesAcciones", self.fecha)
            print("Cantidad listaValoresActualesAcciones en Inicio: " + str(len(self.lista)))
            print(self.listaValoresActualesAcciones)

        self.APERTURA = datetime.combine(fecha, self.horarioApertura)
        self.logger.debug("Apertura: "+str(self.APERTURA))

        self.dolar_ccl_promedio = (self.calculo_ccl_AlCierreARG("GGAL.BA") + self.calculo_ccl_AlCierreARG(
            "YPFD.BA") + self.calculo_ccl_AlCierreARG("BMA.BA") + self.calculo_ccl_AlCierreARG("PAMP.BA")) / 4

        ## Guardo fecha y ccl de ultimo cierre

        if not self.siExiste(self.listaccl, self.fechaUltimoCierreLocal):
            self.listaccl.append([self.fechaUltimoCierreLocal, self.dolar_ccl_promedio])
        self.dao.load(self.listaccl,"listaccl", self.fecha)

        self.cargar_ValoresArbitrados()

        print(" CCL: "+str(self.dolar_ccl_promedio))
        self.dao.getComprasVentasfromFile(self.compras, self.ventas, self.fecha, self.iol)

        print("Fecha: " + self.fecha.strftime('%d/%m/%Y %H:%M:%S'))
        self.logger.info("INICIANDO LARVA " + self.fecha.strftime('%d/%m/%Y %H:%M:%S'))
        print("\n\n**CCL al cierre anterior, "+str(self.fechaUltimoCierreLocal)+", (GGAL, YPFD, BMA, PAMP) Promedio: ${0:.2f}".format(self.dolar_ccl_promedio))
        self.logger.info("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))


    ### Varialiones de los principales indices.
    def getPrincipalesIndices(self,fecha):
        start = fecha - timedelta(days=4)
        end = fecha

        for campo in self.listaIndices:
            ind = campo[0]
            df = yf.download(ind, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            try:
                cierreAnterior = float(df.drop(fecha.date()).tail(1)['Close'].values[0])
            except KeyError:
                cierreAnterior = float(df.tail(1)['Close'].values[0])

            campo[2] = cierreAnterior

            fin = float(yf.download(ind, period=fecha.strftime('%Y-%m-%d'), interval='1m').tail(1)['Close'].values[0])
            campo[3] = fin

            prop = ((fin - cierreAnterior) / fin) * 100
            self.logger.info(campo[1]+" - "+campo[0]+": Variacion ultimo cierre: {0:.2f} %".format(prop))

    ## Carga en la lista las cotizaciónes actuales de los indices
    def getCotizActualIndices(self, fecha):
        for campo in self.listaIndices:
            fin = float(yf.download(campo[0], period=fecha.strftime('%Y-%m-%d'), interval='1m').tail(1)['Close'].values[0])
            campo[3] = fin



    ## Toma configuracion de un archivo
    def getConfig(self):
        with open('config.json', 'r') as file:
            config = json.load(file)
        self.PATH = config['DEFAULT']['PATH']
        self.TIMEREFRESH = config['DEFAULT']['TIMEREFRESH']
        self.PERIODOVENTAFORZADAMIN = config['DEFAULT']['PERIODOVENTAFORZADAMIN']
        self.GANANCIAPORCENTUAL = config['DEFAULT']['GANANCIAPORCENTUAL']
        self.PORCENTUALINDICES = config['DEFAULT']['PORCENTUALINDICES']
        self.FECHALIMITECOMPRA11 = config['DEFAULT']['FECHALIMITECOMPRA11']

    ## LOGGER
    def loguear(self):
        handler = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", "larva.log"))
        #handler = logging.StreamHandler()
        formatter = logging.Formatter(' %(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s ')
        handler.setFormatter(formatter)
        root = logging.getLogger("logueador")
        root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
        root.addHandler(handler)

        return root

    ##
    # Metodo que te carga el valor arbitrado de todos los tickers en la lista.
    def cargar_ValoresArbitrados(self):
        for campo in self.lista:
            valor_arbitrado = float(self.calculo_valor_arbitrado(campo[1],self.dolar_ccl_promedio))
            campo[5] = valor_arbitrado

    ## Carga cotizaciones del cierre anterior en lista.
    ## ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO)
    def cargar_cotiz(self, fecha):
        self.logger.debug('Cargando cotizaciones ultimo cierre.')
        #lista_aux=[]
        start = fecha - timedelta(days=5)
        end = fecha
        for campo in self.lista:
            ## Tomo la ultima cotización local.
            local_ca = 0
            try:
                pd_local_aux = yf.download(campo[1], start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), interval="1d")
                pd_local = pd_local_aux.drop(fecha.date()).tail(1)
            except KeyError:
                self.logger.debug("No se pudo borrar el dia de hoy. "+ campo[1])
                pd_local = pd_local_aux.tail(1)
            if  not pd_local.empty:
                local_ca = pd_local['Close'].values[0]
                np_date = pd_local.index.values[0]
                self.fechaUltimoCierreLocal = numpy.datetime_as_string(np_date, "D")
                self.logger.debug(self.fechaUltimoCierreLocal + " - " + campo[1] + " C. Loc ULT CIERRE {0:.2f}".format(local_ca))

            ## Tomo la ultima cotizacion ADR.
            adr_ca = 0
            try:
                pd_adr_aux = yf.download(campo[0], start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'),
                                           interval="1d")
                pd_adr = pd_adr_aux.drop(fecha.date()).tail(1)
            except KeyError:
                self.logger.debug("No se pudo borrar el dia de hoy. " + campo[0])
                pd_adr = pd_adr_aux.tail(1)
            if not pd_adr.empty:
                adr_ca = pd_adr['Close'].values[0]
                np_date = pd_adr.index.values[0]
                self.fechaUltimoCierreAdr = numpy.datetime_as_string(np_date, "D")
                self.logger.debug(self.fechaUltimoCierreAdr + " - " + campo[0] + " C. ADR ULT CIERRE {0:.2f}".format(adr_ca))


            ##Con esta linea me traigo el ADR del mismo dia del local
            #pd_adr = yf.download(campo[0], start=numpy.datetime_as_string(np_date, "D"), interval="1d").head(1)


            campo[3] = adr_ca
            campo[4] = local_ca
        return None

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
        self.logger.debug(tickerlocal + " C. ADR: {0:.2f}".format(cotizadrf) + " C. Loc: {0:.2f}".format(cotizlocalf) + ' Fac.: ' + str(factor) + " CCL: {0:.2f}".format(resultado))
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

     ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    def getTodasLasCotizaciones(self):
        body = self.iol.getCotizAccionesTodas()

        if body == "":
            return 0

        l = []
        for campo in self.lista:
            for campoBody in body['titulos']:
                ticker = campo[1].split(".")[0]
                if ticker == campoBody['simbolo']:
                    puntas = campoBody['puntas']
                    punta_cantCompra = 0
                    punta_precioCompra = 0
                    punta_cantVenta = 0
                    punta_precioVenta = 0
                    try:
                        punta_cantCompra = puntas['cantidadCompra']
                        punta_precioCompra = puntas['precioCompra']
                        punta_cantVenta = puntas['cantidadVenta']
                        punta_precioVenta = puntas['precioVenta']
                    except:
                        self.logger.warning("Lista de puntas incompleta. Se cargan valores en Cero. ")

                    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ultimoPrecio = campoBody['ultimoPrecio']
                    l.append((ticker, ultimoPrecio, punta_cantCompra, punta_precioCompra,
                                   punta_cantVenta, punta_precioVenta, ahora))
                    break
        #self.logger.debug("Se cargaron todas las cotizaciónes desde IOL, total "+str(len(l)))
        self.listaValoresActualesAcciones = l

    ## ADRs
    ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    def getTodasLasCotizacionesADRs(self):
        body = self.iol.getCotizAdrsTodas()
        l = []
        for campo in self.lista:
            for campoBody in body['titulos']:
                ticker = campo[1].split(".")[0]
                if ticker == campoBody['simbolo']:
                    puntas = campoBody['puntas']
                    punta_cantCompra = 0
                    punta_precioCompra = 0
                    punta_cantVenta = 0
                    punta_precioVenta = 0
                    try:
                        punta_cantCompra = puntas['cantidadCompra']
                        punta_precioCompra = puntas['precioCompra']
                        punta_cantVenta = puntas['cantidadVenta']
                        punta_precioVenta = puntas['precioVenta']
                    except:
                        self.logger.warning("Lista de puntas incompleta. ")

                    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ultimoPrecio = campoBody['ultimoPrecio']
                    l.append((ticker, ultimoPrecio, punta_cantCompra, punta_precioCompra,
                              punta_cantVenta, punta_precioVenta, ahora))
                    break
        self.listaValoresActualesAdrs = l

    ## devuelve: ULTIMOPRECIO, punta_precioCompra, punta_cantCompra, punta_precioVenta, punta_cantVenta
    def getCotizacion(self, tickerlocal):
        for campo in self.listaValoresActualesAcciones:
            if campo[0] == tickerlocal:
                return [campo[1], campo[3], campo[2], campo[5], campo[4]]
        self.logger.warning("NO encontro el ticker: "+tickerlocal)
        return [0,0,0,0,0]


    ## Devuelve True si los indices cumplen con la condicion
    # TODO: por ahora solo tomo el SP500 como indice referencia.
    def condicionIndicesMundiales(self):
        propSP500 = self.calculoPropIndice()

        if propSP500 >= self.PORCENTUALINDICES:
            self.logger.info("Se habilita la compra. SP500 {0:.2f}%".format(propSP500)+" mayor a: {0:.2f}% ".format(self.PORCENTUALINDICES))
            return True
        else:
            self.logger.info("Bloqueo la compra. SP500 {0:.2f}% ".format(propSP500))
            return False


    def calculoPropIndice(self):
        return ((self.listaIndices[0][3] - self.listaIndices[0][2]) / self.listaIndices[0][3]) * 100

    ## Devuelve true si hay compras pendientes de venta. falso en caso contrario
    def isComprasPendientes(self):
        for campo in self.compras:
            if not campo[5]: return True
        return False

    def isHorarioCompra(self):
        now = datetime.now()
        minutosTranscurridos = (now - self.APERTURA).seconds / 60

        if now <= self.APERTURA:
            print("La rueda no abrio.")
            return True


        #if 0 <= minutosTranscurridos and (minutosTranscurridos <= self.PERIODOCOMPRA):
        if (minutosTranscurridos <= self.PERIODOCOMPRA):

            self.logger.info(" Tiempo de compra: " + str(minutosTranscurridos))
            return True
        else:
            self.logger.info(" Termino periodo de compra. ")
            return False


    ## Metodo que permite hacer seguimietno ONLINE de ARB.
    def larva(self):
        fecha = self.fecha
        threadvendedor = threading.Thread(target=self.worker_venta, name="HiloVentas")
        threadvendedor.start()

        self.logger.debug("Arranca larva: ")

        ## Inicio Routing
        if (self.CONRUTEO):
            r = RoutingOrder(self.compras, self.ventas, False, self.logger)
        ###
        ### Bucle principal ##############################################################
        while (True):
            ahora = self.fecha.strftime('%d/%m/%Y %H:%M:%S')
            print("\tFecha: "+ahora)

            self.getConfig()

            print(Fore.BLUE+"\nCompras: "+str(self.compras)+Fore.RESET)
            self.getTodasLasCotizaciones()

            ## Actualizo los valores actuales de los indices.
            self.getCotizActualIndices(fecha)

            ## Actualizo horario de compra
            self.enPeriodoCompra = self.isHorarioCompra()

            if self.enPeriodoCompra:
                if self.condicionIndicesMundiales():
                    for tt in self.lista: ## ITERO POR TICKER
                        tickerlocal = tt[1].split(".")[0]
                        local_up, punta_precioCompra, punta_cantidadCompra, punta_precioVenta, punta_cantidadVenta = self.getCotizacion(tickerlocal)

                        valor_arbi = float(tt[5])
                        cotizlocalf = float(local_up)

                        diferencia = float(valor_arbi)-float(cotizlocalf)
                        variacion = float((diferencia)*100)/float(cotizlocalf)

                        if (variacion >= self.DIFPORCENTUALMINCOMPRA):
                            ## Imprimo ticker con posibilidad de compra.
                            print(Fore.BLUE+tickerlocal + " => LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi) + " - VAR: {0:.2f}%".format(variacion)+Fore.RESET)

                            self.logger.info(tickerlocal + " * LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi)+" - VAR: {0:.2f}%".format(variacion))
                            ##################
                            ### Proceso Compra
                            valorCompraMax, valorVentaMin = self.calculoValoresCompraYVenta(tickerlocal, cotizlocalf, valor_arbi)

                            if valorCompraMax != 0 and punta_precioVenta != 0 and valorCompraMax >= punta_precioVenta and not self.siExiste(self.compras, tickerlocal):
                                #cantidad = self.MONTOCOMPRA // cotizlocalf
                                cantidad = 1
                                print(Fore.GREEN + " AVISO: Comprar: {0:.2f}".format(cantidad)+ " - PUNTAS:  *VENTA - Cant: {0:.2f}".format(punta_cantidadVenta) + ", valor: {0:.2f}".format(punta_precioVenta)+" *COMPRA - Cant: {0:.2f}".format(punta_cantidadCompra) + ", valor: {0:.2f}".format(punta_precioCompra) + Fore.RESET)
                                self.compra(tickerlocal, cotizlocalf, cantidad, valorVentaMin)
                        else:
                            print(tickerlocal + " => LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi)+" - VAR: {0:.2f}%".format(variacion))
                            self.logger.info(tickerlocal + " * LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi)+" - VAR: {0:.2f}%".format(variacion))
                    ## TIEMPO DEL CICLO
                    print(Fore.RED+"\n ...Hilo ppal(de compra) en ejecucion..."+datetime.now().strftime('%d/%m/%Y %H:%M:%S')+Fore.RESET)
                else:
                    print("Se Bloquea la compra. SP500 {0:.2f}%".format(self.calculoPropIndice()) + " menor a: {0:.2f}% ".format(self.PORCENTUALINDICES))
            else:
                print("Termino periodo de compra. ")
                if not self.isComprasPendientes() and self.MODOTEST == 0:
                    self.logger.info("**FIN HILO COMPRAS**")
                    print("** FIN HILO COMPRAS ** ")
                    self.FINVENTAS = True
                    return

            ti.sleep(self.TIMEREFRESH)

    ## Metodo que implementa el Hilo de Venta
    def worker_venta(self):
        ## Hilo de VENTA
        ## Recorre lista de compras
        self.logger.debug("Inicio worker venta")
        while (True):
            if (len(self.compras) == 0):
                self.logger.debug("NO HAY COMPRAS HECHAS")
            else:
                self.logger.debug("Compras pendientes de venta: {0:.2f}".format(float(len(self.compras)-len(self.ventas))))
                self.xventa()

            self.logger.info("...Hilo venta en ejecucion... "+datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            if self.FINVENTAS and not self.isComprasPendientes():
                self.logger.info("**FIN HILO VENTAS**")
                print("** FIN HILO VENTAS ** ")
                return
            ti.sleep(self.TIMEREFRESH)


    ## Metodo que compara el objetivo de venta con el precio de la punta de compra. Si es menor manda la compra.
    def xventa(self):
        for compra in self.compras:
                if compra[4] == Estado.OPERADA and not self.seVendio(compra[0]):
                    local_up, punta_precioCompra, punta_cantidadCompra, punta_precioVenta, punta_cantidadVenta = self.getCotizacion(compra[0])

                    ##Logica que tiene en cuenta el tipo que hace que esta comprado y cambia el ValorMinVenta
                    self.gradientePrecioVenta(compra)
                    self.logger.info("Ticker: "+compra[0]+" Punta de compra: $ {0:.2f}".format(punta_precioCompra)+" Objetivo: $ {0:.2f}".format(compra[6]))

                    if punta_precioCompra !=0 and punta_precioCompra >= compra[6]:
                        print(Fore.BLUE+"\tObjetivo Venta CUMPLIDO: "+compra[0]+" Valor: {0:.2f}".format(punta_precioCompra)+Fore.RESET)
                        self.logger.info("Objetivo Venta CUMPLIDO: "+compra[0]+" Valor: {0:.2f}".format(punta_precioCompra))
                        if (punta_cantidadCompra < compra[2]):
                            self.logger.debug("La cantidad de la punta de compra es menor a la cantidad que se quiere vender. VER")
                        self.vender(compra, punta_precioCompra)

    ## Metodo que agrega a la
    def vender(self, compra, valor):
        ticker = compra[0]
        cantidad = compra[2]
        if not self.siExiste(self.ventas, ticker):
            self.logger.debug("Envio VENTA: " + ticker + " Cantidad: {0:.2f}".format(cantidad) + " Valor: {0:.2f}".format(valor))
            self.agregarVenta(ticker, valor, cantidad)
            print(Fore.GREEN + "\tVenta Finalizada: " + ticker + " Valor: {0:.2f}".format(valor)+ " Cantidad: {0:.2f}".format(cantidad) + Fore.RESET)
        else:
            self.logger.debug("Esta venta ya fue hecha.")
            ##TODO: Ver como hacer para borrar una orden de venta a la cual hay que cambiarle el valor.

        return None


        ## Agrega la venta a la lista. Actualiza el estado de la compra y persiste en disco.
    def agregarVenta(self, ticker, valor, cantidad):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ventas.append([ticker, valor, cantidad, "000", Estado.ENPROCESO, ahora])
        self.actualizarVentas(self.ventas, self.fecha)

    ## En funcion del tiempo que hace que esta comprado el papel baja el valorMinVenta.
    def gradientePrecioVenta(self, compra):
        ahora = datetime.now()
        horarioCompra = compra[5]

        difCompra = ahora - datetime.strptime(horarioCompra,"%Y-%m-%d %H:%M:%S")
        valorCompra = compra[1]
        costoCompra = valorCompra + self.iol.calculoCostoOp(valorCompra)
        difObjetivo = compra[6] - costoCompra
        descuento = difObjetivo / 3

        #self.logger.info(campo[0]+" Costo TOTAL compra: $ {0:.2f} (incluye costos broker)".format(costoCompra))
        nuevoValor = compra[6]

        if  self.MINUTEGRADIENTEVENTA <= (difCompra.seconds/60) and (difCompra.seconds/60) < (2*self.MINUTEGRADIENTEVENTA):
            nuevoValor = compra[6] - descuento
            self.logger.info(compra[0] + " Ejecuto Gradiente N1, decuento: ${0:.2f}".format(
            descuento) + " Nuevo ValorVentaMin: ${0:.2f}".format(nuevoValor) + " (anterior: ${0:.2f})".format(
            compra[6]))

        elif (2*self.MINUTEGRADIENTEVENTA)<=(difCompra.seconds/60) and (difCompra.seconds/60) <= (4*self.MINUTEGRADIENTEVENTA)  :
            nuevoValor = compra[6] - (2 * descuento)
            self.logger.info(compra[0] + " Ejecuto Gradiente N2, decuento: ${0:.2f}".format(
            2 * descuento) + " Nuevo ValorVentaMin: ${0:.2f}".format(
                nuevoValor) + " (anterior: ${0:.2f})".format(compra[6]))

        elif (4*self.MINUTEGRADIENTEVENTA) < (difCompra.seconds/60) :
            nuevoValor = compra[6] - (3 * descuento)
            self.logger.info(compra[0] + " Ejecuto Gradiente N3, decuento: ${0:.2f}".format(
            3 * descuento) + " Nuevo ValorVentaMin: ${0:.2f}".format(
                nuevoValor) + " (anterior: ${0:.2f})".format(compra[6]))

        ## 16:00 intento vender al costo de compra.
        if (ahora >=self.APERTURA):
            difAperturaMin = (ahora - self.APERTURA).seconds / 60
        else:
            difAperturaMin = 0
        self.logger.info(" Minutos desde la apertura: {0:.2f} ".format(difAperturaMin))

        if self.PERIODOVENTAFORZADAMIN <= difAperturaMin and difAperturaMin < 345:
            nuevoValor = costoCompra
            self.logger.info(compra[0] + " Ejecuto Gradiente Final, Nuevo ValorVentaMin: ${0:.2f}".format(nuevoValor))

        '''
        ## Gradientes con perdida.
        ## 16:45

        if 345 <= difAperturaMin and difAperturaMin < 350:
            descuento5 = costoCompra * 5 / 100
            totalDescuento5 = (costoCompra-descuento5) * compra[2]
            if totalDescuento5 <= self.ganancia:
                nuevoValor = costoCompra - descuento5
                self.logger.info(compra[0] + " Ejecuto Gradiente c/Perdida, Nuevo ValorVentaMin: ${0:.2f}".format(nuevoValor))
            else: self.logger.info(compra[0] + " Gradiente c/Perdida 16:45 sin saldo")
        ## 16:50
        if 350 <= difAperturaMin and difAperturaMin < 355:
            descuento10 = costoCompra * 10 / 100
            totalDescuento10 = (costoCompra - descuento10) * compra[2]
            if totalDescuento10 <= self.ganancia:
                nuevoValor = costoCompra - descuento10
                self.logger.info(compra[0] + " Ejecuto Gradiente c/Perdida, Nuevo ValorVentaMin: ${0:.2f}".format(nuevoValor))
            else: self.logger.info(compra[0] + " Gradiente c/Perdida 16:50 sin saldo")

        ## 16:55
        if 355 <= difAperturaMin:
            descuento15 = costoCompra * 15 / 100
            totalDescuento15 = (costoCompra - descuento15) * compra[2]
            if totalDescuento15 <= self.ganancia:
                nuevoValor = costoCompra - descuento15
                self.logger.info(compra[0] + " Ejecuto Gradiente c/Perdida, Nuevo ValorVentaMin: ${0:.2f}".format(nuevoValor))
            else: self.logger.info(compra[0] + " Gradiente c/Perdida 16:55 sin saldo")
        '''
        if (nuevoValor != compra[6]):
            compra[6] = nuevoValor
            self.actualizarCompras()

        return None

    ## Calcula el punto medio entre el valor y el arbitrado y se mueve 0,5 para cada lado
    def calculoValoresCompraYVenta(self, ticker, valor, valorArbitrado):
        medio = (valorArbitrado + valor) / 2
        valorCompraMax = medio - (medio * (self.GANANCIAPORCENTUAL/2) / 100)
        valorVentaMin = medio + (medio * (self.GANANCIAPORCENTUAL/2) / 100)

        self.logger.debug(ticker+" COTIZ ACTUAL: $ {0:.2f}".format(valor)+"\t Valor compra Maximo {0:.2f}".format(valorCompraMax)+" -- Valor venta Minimo {0:.2f}".format(valorVentaMin))

        return [valorCompraMax, valorVentaMin]


    ## Orden que envia a comprar y agrega a la lista de operaciones pendientes.
    def compra(self, ticker, valor, cantidad, valorVentaMin):
            self.logger.debug("COMPRA: " + ticker + " Cantidad: {0:.2f}".format(cantidad) + " Valor: {0:.2f}".format(valor))
            self.agregarCompra(ticker, valor, cantidad, valorVentaMin)
            costoOperacion = self.iol.calculoCostoOp(valor)
            self.logger.info("Costo compra: {0:.2f}".format(costoOperacion))
            print("Comprado!!!")


    def seVendio(self, ticker):
        for tt in self.ventas:
            if (tt[0] == ticker and tt[4] == Estado.OPERADA): return True
        return False


    ## Busqueda generica
    def siExiste(self, lista, ticker):
        for tt in lista:
            if (tt[0] == ticker): return True
        return False

    ## Busqueda generica que devuelve el elemento buscado si existe
    def buscar(self, lista, ticker):
        for tt in lista:
            if (tt[0] == ticker): return tt
        return None

    ## Imprime el listado de compras hechas
    def printCompras(self):
        print(self.compras)

    ## Agrega la compra a la lista. Persiste la lista en disco.
    def agregarCompra(self, ticker, valor, cantidad, valorVentaMin):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.compras.append([ticker, valor, cantidad, "000", Estado.ENPROCESO, ahora, valorVentaMin])
        self.dao.actualizarCompras(self.compras, self.fecha)

    def larvaBackTest(self, fecha):
        self.logger.info("Ejecutando Backtest.")

        self.logger.debug("Arranca larva: ")

        for campo in self.lista:
            ticker = campo[1]
            print("\t"+ticker)

            fechaS = fecha.strftime('%Y-%m-%d')
            dia = timedelta(days=1)
            fechaE = (fecha + dia).strftime('%Y-%m-%d')
            listaCotizaciones = yf.download(ticker, start=fechaS, end=fechaE, interval='5m')

            for x in range(len(listaCotizaciones)):
                hora = listaCotizaciones.index[x]
                precio = listaCotizaciones.iloc[x]['Close']
                valor_arbi = float(campo[5])
                cotizlocalf = float(precio)
                diferencia = float(valor_arbi) - float(cotizlocalf)
                variacion = float((diferencia) * 100) / float(cotizlocalf)
                if (variacion >= self.DIFPORCENTUALMINCOMPRA):
                    ### Proceso Compra
                    valorCompraMax, valorVentaMin = self.calculoValoresCompraYVenta(ticker, cotizlocalf, valor_arbi)
                    if valorCompraMax != 0 and cotizlocalf != 0 and valorCompraMax >= cotizlocalf and not self.siExiste(self.compras, ticker):
                        #cantidad = self.MONTOCOMPRA // cotizlocalf
                        cantidad = 1
                        print(Fore.GREEN +str(hora)+ " AVISO: Comprar: {0:.2f}".format(cantidad)+", valor: {0:.2f}".format(cotizlocalf) + Fore.RESET)
                        self.compra(ticker, cotizlocalf, cantidad, valorVentaMin)

                for campo in self.compras:
                    if not self.siExiste(self.ventas,ticker):
                        valorMinVenta = campo[6]
                        if cotizlocalf != 0 and cotizlocalf >= valorMinVenta:
                            self.vender(campo[0], cotizlocalf, campo[2])
                            campo[5]=True


lista=[]
#ahora = datetime.now()
#listaC = yf.download('BMA.BA',start='2020-5-19', end='2020-5-20',interval='1d')

#for x in range(len(listaC)):
#    fechaS = str(listaC.index[x])[0:10]
#    fecha = datetime.strptime(fechaS, '%Y-%m-%d')
#    a = AADR(lista, fecha)
#    a.larvaBackTest(fecha)


#PRODUCCION
#ahora = datetime.now()
#a = AADR(lista, ahora)
#a.compra('BMA',200, 20, 202)
#ti.sleep(5)
#a.vender(('BMA',280,1,"000", Estado.ENPROCESO, ahora), 300)
#a.agregarVenta("BMA", 300, 1)
#a.larva()
