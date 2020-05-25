# -*- coding: utf-8 -*-
import json
import logging
import logging.handlers
import pickle
import time as ti
from datetime import datetime, date, timedelta, time
import threading
import numpy
import yfinance as yf
from colorama import Fore
import os
from finance_dao import Iol

class AADR(object):
    lista = [] ##Lista que mantiene cotizaciónes al cierre anterior ## ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO)
    compras = [] ##  ( TICKER, VALOR, CANTIDAD, NROOPERACION, VALORVENTAMIN, TIMESTAMP)
    ventas = [] ##   ( TICKER, VALOR, CANTIDADm NROOPERACION, TIMESTAMP)
    listaValoresActualesAcciones = [] ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    listaValoresActualesAdrs = [] ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    TIMEREFRESH = 10
    MONTOCOMPRA = 2000
    GANANCIAPORCENTUAL = 1 #Constante que defije objetivo de ganancia relativa porcentual
    DIFPORCENTUALMINCOMPRA = GANANCIAPORCENTUAL+1 #Minima diferencia con el valor arbitrado par considerarlo en la compra.
    MODOTEST = 1
    FECHALIMITECOMPRA11 = 15
    MINUTEGRADIENTEVENTA = 30
    APERTURA = 0
    PERIODOCOMPRA = MINUTEGRADIENTEVENTA

    def __init__(self,lista):
        self.loguear()
        if (self.MODOTEST != 1):
            self.lista=lista
            self.lista.append(('GGAL','GGAL.BA',10,0,0,0))
            self.lista.append(('YPF','YPFD.BA',1,0,0,0))
            self.lista.append(('BMA','BMA.BA',10,0,0,0))
            self.lista.append(('PAM','PAMP.BA',25,0,0,0))
            self.lista.append(('BBAR','BBAR.BA',3,0,0,0))
            self.lista.append(('CEPU','CEPU.BA',10,0,0,0))
            self.lista.append(('CRESY','CRES.BA',10,0,0,0))
            self.lista.append(('EDN','EDN.BA',20,0,0,0))
            self.lista.append(('SUPV','SUPV.BA',5,0,0,0))
            self.lista.append(('TEO','TECO2.BA',5,0,0,0))
            self.lista.append(('TGS','TGSU2.BA',5,0,0,0))
            self.lista.sort()
            self.cargar_cotiz()

            ## Guardo la lista
            with open("lista.dat", "wb") as f:
                pickle.dump(self.lista, f)

            ## Guardo la listaValoresActualesAcciones
            with open("listaValoresActualesAcciones.dat", "wb") as f:
                pickle.dump(self.listaValoresActualesAcciones, f)

        else:
            ##Cargo lista desde archivo
            with open("lista.dat", "rb") as f:
                self.lista = pickle.load(f)
            print("Cantidad lista en Inicio: " + str(len(self.lista)))
            print(self.lista)

            ##Cargo listaValoresActualesAcciones desde archivo
            with open("listaValoresActualesAcciones.dat", "rb") as f:
                self.listaValoresActualesAcciones = pickle.load(f)
            print("Cantidad listaValoresActualesAcciones en Inicio: " + str(len(self.lista)))
            print(self.listaValoresActualesAcciones)


        hoy = datetime.now()
        once = time(hour=11, minute=0, second=0)
        self.APERTURA = datetime.combine(hoy, once)
        logging.info("Apertura: "+str(self.APERTURA))


        self.dolar_ccl_promedio = (self.calculo_ccl_AlCierreARG("GGAL.BA") + self.calculo_ccl_AlCierreARG(
            "YPFD.BA") + self.calculo_ccl_AlCierreARG("BMA.BA") + self.calculo_ccl_AlCierreARG("PAMP.BA")) / 4
        self.cargar_ValoresArbitrados()


        self.hoy = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        print("Fecha: " + self.hoy)
        logging.info("INICIANDO LARVA " + self.hoy)
        print("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))
        logging.info("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))

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


    ## LOGGER
    def loguear(self):
        #handler = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", "./larva.log"))
        handler = logging.StreamHandler()
        formatter = logging.Formatter(' %(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s ')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
        root.addHandler(handler)

    ##
    # Metodo que te carga el valor arbitrado de todos los tickers en la lista.
    def cargar_ValoresArbitrados(self):
        logging.debug("Calculando CCL al cierre anterior")
        lista_aux=[]
        for campo in self.lista:
            valor_arbitrado = float(self.calculo_valor_arbitrado(campo[1],self.dolar_ccl_promedio))
            campo_aux=(campo[0], campo[1], campo[2], campo[3], campo[4], valor_arbitrado)
            lista_aux.append(campo_aux)
        self.lista=lista_aux

    ## Carga cotizaciones del cierre anterior en lista.
    def cargar_cotiz(self):
        logging.debug('Cargando cotizaciones ultimo cierre.')
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
                logging.debug("No se pudo borrar el dia de hoy. "+ campo[1])
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


     ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    def getTodasLasCotizaciones(self):
        iol = Iol()
        body = iol.getCotizAccionesTodas()

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
                        logging.warning("Lista de puntas incompleta. Se cargan valores en Cero. ")

                    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ultimoPrecio = campoBody['ultimoPrecio']
                    l.append((ticker, ultimoPrecio, punta_cantCompra, punta_precioCompra,
                                   punta_cantVenta, punta_precioVenta, ahora))
                    break
        #logging.debug("Se cargaron todas las cotizaciónes desde IOL, total "+str(len(l)))
        self.listaValoresActualesAcciones = l

    ## ADRs
    ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    def getTodasLasCotizacionesADRs(self):
        iol = Iol()
        body = iol.getCotizAdrsTodas()
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
                        logging.error("Lista de puntas incompleta. ")

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
        logging.warning("NO encontro el ticker: "+tickerlocal)
        return [0,0,0,0,0]

    ## Metodo que permite hacer seguimietno ONLINE de ARB.
    def larva(self):
        threadvendedor = threading.Thread(target=self.worker_venta, name="HiloVentas")
        threadvendedor.start()
        logging.debug("Arranca larva: ")
        iol = Iol()
        ###
        ### Bucle principal ##############################################################
        while (True):
            ahoraDate = datetime.now()
            ahora = ahoraDate.strftime('%d/%m/%Y %H:%M:%S')

            print(Fore.BLUE+"\nCompras: "+str(self.compras)+Fore.RESET)
            self.getTodasLasCotizaciones()
            #self.getTodasLasCotizacionesADRs()

            print("Fecha: "+ahora)
            for tt in self.lista:
                tickerlocal = tt[1].split(".")[0]
                local_up, precioCompra, cantidadCompra, punta_precioVenta, punta_cantidadVenta = self.getCotizacion(tickerlocal)

                #local_ca, local_up, precioCompra, cantidadCompra, punta_precioVenta, punta_cantidadVenta = iol.getCotizConPuntas(tickerlocal, mercado="BCBA")

                #adr_ca, adr_up, adr_prop = iol.getCotiz(ticker=tt[0], mercado="NYSE")

                valor_arbi = float(tt[5])
                cotizlocalf = float(local_up)
                cotizadrf = 0 #float(adr_up)

                diferencia = float(valor_arbi)-float(cotizlocalf)
                variacion = float((diferencia)*100)/float(cotizlocalf)

                if (variacion>=self.DIFPORCENTUALMINCOMPRA):
                    print(Fore.BLUE+tickerlocal + "\t\t C LOC. ACTUAL: {0:.2f}".format(cotizlocalf) + "\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion)+Fore.RESET)
                    ##################
                    ### Proceso Compra
                    valorCompraMax, valorVentaMin = self.calculoValoresCompraYVenta(tickerlocal, cotizlocalf, valor_arbi)
                    minutosTranscurridos = (ahoraDate - self.APERTURA).seconds/60

                    if (minutosTranscurridos <= self.PERIODOCOMPRA):
                        logging.info(" Tiempo restante de compra: "+str(minutosTranscurridos))
                    else:
                        logging.info(" Ya no es periodo de compra.")

                    if self.PERIODOCOMPRA >= minutosTranscurridos and valorCompraMax != 0 and punta_precioVenta != 0 and valorCompraMax >= punta_precioVenta:
                        cantidad = self.MONTOCOMPRA // cotizlocalf
                        print(Fore.GREEN + " AVISO: Comprar: {0:.2f}".format(cantidad)+ " - Punta vendedora - Cant: {0:.2f}".format(
                            punta_cantidadVenta) + ", valor: {0:.2f}".format(punta_precioVenta) + Fore.RESET)
                        self.compra(tickerlocal, cotizlocalf, cantidad, valorVentaMin)
                else:
                    print(tickerlocal + "\t\t C LOC. ACTUAL: {0:.2f}".format(cotizlocalf) + "\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion)+Fore.RESET)
                    logging.debug(tickerlocal+ "\t\t C LOC. ACTUAL: {0:.2f}".format(cotizlocalf) + "\t\t C LOC. ARBI: {0:.2f}".format(valor_arbi)+"\t\t C ADR ACTUAL: {0:.2f}".format(cotizadrf)+"\t\t DIF: {0:.2f}".format(float(diferencia))+"\t\t VAR: {0:.2f}%".format(variacion)+Fore.RESET)
            ## TIEMPO DEL CICLO
            print(Fore.RED+"\n ...Hilo ppal en ejecucion..."+datetime.now().strftime('%d/%m/%Y %H:%M:%S')+Fore.RESET)
            ti.sleep(10)

    ## Metodo que implementa el Hilo de Venta
    def worker_venta(self):
        ## Hilo de VENTA
        ## Recorre lista de compras
        logging.debug("Inicio worker venta")
        while (True):
            if (len(self.compras) == 0):
                logging.debug("NO HAY COMPRAS HECHAS")
            else:
                logging.debug("Compras hechas: {0:.2f}".format(len(self.compras)))
                self.xventa()

            logging.info("...Hilo venta en ejecucion..."+datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            ti.sleep(10)


    ## Metodo que compara el objetivo de venta con el precio de la punta de compra. Si es menor manda la compra.
    # TODO: falta ver que pasa cuando la cantidad a comprar es mayor que la punta.
    def xventa(self):
        logging.debug("Reviso todos as compras y miro si alcanzo el valorVentaMin")
        for campo in self.compras:
                ##loc_ca, loc_up, prop=iol.getCotiz(campo[0])
                ## devuelve: ULTIMOPRECIO, punta_precioCompra, punta_cantCompra, punta_precioVenta, punta_cantVenta
                local_up, punta_precioCompra, punta_cantidadCompra, punta_precioVenta, punta_cantidadVenta = self.getCotizacion(campo[0])

                ##Logica que tiene en cuenta el tipo que hace que esta comprado y cambia el ValorMinVenta
                valorMinVenta = self.gradientePrecioVenta(campo)

                logging.info("Ticker: "+campo[0]+" Punta de compra: $ {0:.2f}".format(punta_precioCompra)+" Objetivo: $ {0:.2f}".format(valorMinVenta))

                if (not self.buscar(self.ventas, campo[0])) and punta_precioCompra !=0 and punta_precioCompra >= valorMinVenta:
                    print(Fore.BLUE+"\tObjetivo Venta CUMPLIDO: "+campo[0]+" Valor: {0:.2f}".format(punta_precioCompra)+Fore.RESET)

                    logging.info("Objetivo Venta CUMPLIDO: "+campo[0]+" Valor: {0:.2f}".format(punta_precioCompra))

                    if (punta_cantidadCompra < campo[2]):
                        logging.info("La cantidad de la punta de compra es menor a la cantidad que se quiere vender. VER")

                    self.vender(campo[0], punta_precioCompra, campo[2])

    ## Orden que envia a Vender a IOL y agrega a la lista de operaciones pendientes.
    def vender(self, ticker, valor, cantidad):
        logging.info("Envio orden de VENTA A IOL: " + ticker + " Cantidad: {0:.2f}".format(
            cantidad) + " Valor: {0:.2f}".format(valor))
        if not self.buscar(self.ventas, ticker):
            self.agregarVenta(ticker, valor, cantidad)
            print(Fore.GREEN + "\tVenta Finalizada: " + ticker + " Valor: {0:.2f}".format(valor)+ " Cantidad: {0:.2f}".format(cantidad) + Fore.RESET)
        else:
            print("Venta ya hecha")
            logging.debug("Esta venta ya fue hecha.")
        return 0

    ## En funcion del tiempo que hace que esta comprado el papel baja el valorMinVenta.
    ## compras ( TICKER, VALOR, CANTIDAD, NROOPERACION, VALORVENTAMIN, TIMESTAMP)

    def gradientePrecioVenta(self, campo):
        ahora = datetime.now()
        horarioCompra = campo[5]

        dif = ahora - datetime.strptime(horarioCompra,"%Y-%m-%d %H:%M:%S")
        valorCompra = campo[1]
        costoCompra = valorCompra + self.calculoCostoOp(valorCompra)
        difObjetivo = campo[4] - costoCompra
        descuento = difObjetivo / 3

        logging.info(campo[0]+" Costo TOTAL compra: $ {0:.2f} (incluye costos broker)".format(costoCompra))

        if  self.MINUTEGRADIENTEVENTA <= (dif.seconds/60) and (dif.seconds/60) < (2*self.MINUTEGRADIENTEVENTA):
            logging.info(campo[0]+" Ejecuto Gradiente N1, decuento: ${0:.2f}".format(descuento)+" Nuevo ValorVentaMin: ${0:.2f}".format(campo[4]-descuento)+" (anterior: ${0:.2f})".format(campo[4]))
            return campo[4]-descuento

        elif (2*self.MINUTEGRADIENTEVENTA)<=(dif.seconds/60) and (dif.seconds/60) <= (4*self.MINUTEGRADIENTEVENTA)  :
            logging.info(campo[0]+" Ejecuto Gradiente N2, decuento: ${0:.2f}".format(2*descuento)+" Nuevo ValorVentaMin: ${0:.2f}".format(campo[4]-(2*descuento))+" (anterior: ${0:.2f})".format(campo[4]))
            return campo[4]-(2*descuento)
        elif (dif.seconds/60) >= (4*self.MINUTEGRADIENTEVENTA):
            logging.info(campo[0] + " Ejecuto Gradiente N3, decuento: ${0:.2f}".format(3 * descuento) + " Nuevo ValorVentaMin: ${0:.2f}".format(campo[4] - (3 * descuento)) + " (anterior: ${0:.2f})".format(campo[4]))
            return campo[4] - (3 * descuento)

        return campo[4]


    ## Calcula el punto medio entre el valor y el arbitrado y se mueve 0,5 para cada lado
    def calculoValoresCompraYVenta(self, ticker, valor, valorArbitrado):
        medio = (valorArbitrado + valor) / 2
        valorCompraMax = medio - (medio * (self.GANANCIAPORCENTUAL/2) / 100)
        valorVentaMin = medio + (medio * (self.GANANCIAPORCENTUAL/2) / 100)

        logging.info(ticker+" COTIZ ACTUAL: $ {0:.2f}".format(valor)+"\t Valor compra Maximo {0:.2f}".format(valorCompraMax)+" -- Valor venta Minimo {0:.2f}".format(valorVentaMin))

        return [valorCompraMax, valorVentaMin]


    ## Orden que envia a comprar a IOL y agrega a la lista de operaciones pendientes.
    def compra(self, ticker, valor, cantidad, valorVentaMin):
        logging.info("Envio orden de COMPRA A IOL: "+ticker+" Cantidad: {0:.2f}".format(cantidad)+" Valor: {0:.2f}".format(valor))

        if not self.buscar(self.compras,ticker):
            self.agregarCompra(ticker, valor, cantidad, valorVentaMin)

            costoOperacion = self.calculoCostoOp(valor)
            logging.info("Costo compra: {0:.2f}".format(costoOperacion))
            print("Comprado!!!")
        else:
            print("\tTicket Comprado anteriormente.")
            logging.info("Ticket Comprado anteriormente.")
        return 0

    ## Calcula costos en funcion de los costos de IOL. NO tiene en cuenta la intradiaria
    def calculoCostoOp(self, monto):
        COMISIONBROKER = 0.5/100
        DERECHOMERCADO = 0.08/100
        IVA = 21/100
        return ( (monto * COMISIONBROKER) + (monto * DERECHOMERCADO) + ((monto * COMISIONBROKER) * IVA) + ((monto * DERECHOMERCADO) * IVA))



    ## Busqueda generica
    def buscar(self,lista,ticker):
        for tt in lista:
            if (tt[0] == ticker): return True

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

    def larvaBackTest(self):
        logging.info("Ejecutando Backtest.")

lista=[]
a = AADR(lista)

a.larva()

#a.xcompra("BBAR",139, 100, 100, 232)
#a.xcompra("BBAR",250, 240, 100, 232)
#a.printCompras()
#a.agregarVenta("BMA", 24,1)

#y = Yahoo()
#iol = Iol()

#print(' GGAL YAHOO: '+ str(y.getCotiz('GGAL.BA')))
#print(' GGAL IOL: '+ str(iol.getCotiz('GGAL')))

#dolar_ccl_promedio=(aa.calculo_ccl_AlCierreARG("GGAL.BA")+aa.calculo_ccl_AlCierreARG("YPFD.BA")+aa.calculo_ccl_AlCierreARG("BMA.BA")+aa.calculo_ccl_AlCierreARG("PAMP.BA"))/4
#print("*****Dolar CCL (GGAL, YPFD, BMA, PAMP) Promedio: "+str(dolar_ccl_promedio))

#for tt in aa.lista:
#    valor_arbi = aa.calculo_valor_arbitrado(tt[1],dolar_ccl_promedio)
#    aa.imprimir_resultado(tt[1],valor_arbi)
