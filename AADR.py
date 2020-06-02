# -*- coding: utf-8 -*-
import logging
import logging.handlers
import pickle
import time as ti
from datetime import datetime, timedelta, time
import threading
import numpy
import yfinance as yf
from colorama import Fore
import os
from finance_dao import Iol
import json


class AADR(object):
    lista = [] ##    ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO) ##Lista que mantiene cotizaciónes al cierre anterior ##
    compras = [] ##  ( TICKER, VALOR, CANTIDAD, NROOPERACION, VALORVENTAMIN, VENDIDO, TIMESTAMP)
    ventas = [] ##   ( TICKER, VALOR, CANTIDADm NROOPERACION, TIMESTAMP)
    listaValoresActualesAcciones = [] ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    listaValoresActualesAdrs = [] ## TICKER, ULTIMOPRECIO, punta_cantCompra, punta_precioCompra, punta_cantVenta, punta_precioVenta, TIMESTAMP)
    listaccl = [] ##Lista de historicos CCL.
    fechaUltimoCierre = ""
    TIMEREFRESH = 10
    MONTOCOMPRA = 2000
    GANANCIAPORCENTUAL = 2 #Constante que defije objetivo de ganancia relativa porcentual
    DIFPORCENTUALMINCOMPRA = GANANCIAPORCENTUAL+1 #Minima diferencia con el valor arbitrado par considerarlo en la compra.
    MODOTEST = 0
    FECHALIMITECOMPRA11 = 20
    MINUTEGRADIENTEVENTA = 45
    APERTURA = 0
    PERIODOCOMPRA = FECHALIMITECOMPRA11 ## Periodo maximo de compra.
    PERIODOVENTA = 5 * 60 ## 16hs comienza el horario de venta a costo.

    def __init__(self, lista, fecha):
        self.loguear()
        self.fecha = fecha
        self.iol = Iol()
        self.getConfig()

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
            with open(self.PATH+"lista"+self.fecha.strftime('%d%m%Y')+".dat", "wb") as f:
                pickle.dump(self.lista, f)
            ## Guardo la listaValoresActualesAcciones
            with open(self.PATH+"listaValoresActualesAcciones"+self.fecha.strftime('%d%m%Y')+".dat", "wb") as f:
                pickle.dump(self.listaValoresActualesAcciones, f)
        else: # MODO TEST
            ##Cargo lista desde archivo
            try:
                with open(self.PATH+"lista"+self.fecha.strftime('%d%m%Y')+".dat", "rb") as f:
                    self.lista = pickle.load(f)
            except Exception:
                pickle.dump(self.lista, open(self.PATH+"lista"+self.fecha.strftime('%d%m%Y')+".dat", "wb"))

            print("Cantidad lista en Inicio: " + str(len(self.lista)))
            print(self.lista)

            ##Cargo listaValoresActualesAcciones desde archivo
            try:
                with open(self.PATH+"listaValoresActualesAcciones"+self.fecha.strftime('%d%m%Y')+".dat", "rb") as f:
                    self.listaValoresActualesAcciones = pickle.load(f)
            except Exception:
                pickle.dump(self.lista, open(self.PATH+"listaValoresActualesAcciones" + self.fecha.strftime('%d%m%Y') + ".dat", "wb"))

            print("Cantidad listaValoresActualesAcciones en Inicio: " + str(len(self.lista)))
            print(self.listaValoresActualesAcciones)


        once = time(hour=11, minute=0, second=0)
        self.APERTURA = datetime.combine(fecha, once)
        logging.debug("Apertura: "+str(self.APERTURA))

        self.dolar_ccl_promedio = (self.calculo_ccl_AlCierreARG("GGAL.BA") + self.calculo_ccl_AlCierreARG(
            "YPFD.BA") + self.calculo_ccl_AlCierreARG("BMA.BA") + self.calculo_ccl_AlCierreARG("PAMP.BA")) / 4

        ## Guardo fecha y ccl de ultimo cierre
        if not self.siExiste(self.listaccl, self.fechaUltimoCierre):
            self.listaccl.append([self.fechaUltimoCierre, self.dolar_ccl_promedio])
        with open(self.PATH+"listaccl.dat", "wb") as f:
            pickle.dump(self.listaccl, f)

        self.cargar_ValoresArbitrados()

        print(" CCL: "+str(self.dolar_ccl_promedio))

        print("Fecha: " + self.fecha.strftime('%d/%m/%Y %H:%M:%S'))
        logging.info("INICIANDO LARVA " + self.fecha.strftime('%d/%m/%Y %H:%M:%S'))
        print("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))
        logging.info("\n\n**CCL al cierre anterior: (GGAL, YPFD, BMA, PAMP) Promedio: {0:.2f}".format(self.dolar_ccl_promedio))

        ##Cargo compras desde archivo
        try:
            with open(self.PATH+"compras"+self.fecha.strftime('%d%m%Y')+".dat", "rb") as f:
                self.compras = pickle.load(f)
        except Exception:
            pickle.dump(self.compras, open(self.PATH+"compras" + self.fecha.strftime('%d%m%Y') + ".dat", "wb"))

        print("Cantidad compras en Inicio: "+str(len(self.compras)))
        print(self.compras)

        ##Cargo ventas desde archivo
        try:
            with open(self.PATH+"ventas"+self.fecha.strftime('%d%m%Y')+".dat", "rb") as f:
                self.ventas = pickle.load(f)
        except Exception:
            pickle.dump(self.ventas, open(self.PATH+"ventas" + self.fecha.strftime('%d%m%Y') + ".dat", "wb"))

        print("Cantidad ventas en Inicio: "+str(len(self.ventas)))
        print(self.ventas)

    ## Toma configuracion de un archivo
    def getConfig(self):
        with open('config.json', 'r') as file:
            config = json.load(file)
        self.PATH = config['DEFAULT']['PATH']

    ## LOGGER
    def loguear(self):
        #handler = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", "larva.log"))
        handler = logging.StreamHandler()
        formatter = logging.Formatter(' %(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s ')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
        root.addHandler(handler)

    ##
    # Metodo que te carga el valor arbitrado de todos los tickers en la lista.
    def cargar_ValoresArbitrados(self):
        for campo in self.lista:
            valor_arbitrado = float(self.calculo_valor_arbitrado(campo[1],self.dolar_ccl_promedio))
            campo[5] = valor_arbitrado

    ## Carga cotizaciones del cierre anterior en lista.
    ## ( TICKER EXTRANGERO, TICKER LOCAL, FACTOR, COTIZ ADR CIERRE ANTEIOR, COTIZ LOCAL CIERRE ANTERIOR, VALOR ARBITRADO)
    def cargar_cotiz(self, fecha):
        logging.debug('Cargando cotizaciones ultimo cierre.')
        #lista_aux=[]
        start = fecha - timedelta(days=3)
        end = fecha
        for campo in self.lista:
            local_ca = 0
            adr_ca = 0
            try:
                pd_local_aux = yf.download(campo[1], start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), interval="1d")
                pd_local = pd_local_aux.drop(fecha.date()).tail(1)
            except KeyError:
                logging.debug("No se pudo borrar el dia de hoy. "+ campo[1])
                pd_local = pd_local_aux.tail(1)

            if  not pd_local.empty:
                local_ca = pd_local['Close'].values[0]
                np_date = pd_local.index.values[0]
                self.fechaUltimoCierre = numpy.datetime_as_string(np_date, "D")
                logging.debug("Calculo CCL al dia: "+self.fechaUltimoCierre)

                ##Con esta linea me traigo el ADR del mismo dia del local
                pd_adr = yf.download(campo[0], start=numpy.datetime_as_string(np_date, "D"), interval="1d").head(1)

                if not pd_adr.empty:
                    adr_ca = pd_adr['Close'].values[0]
            logging.debug(self.fechaUltimoCierre+ " - "+campo[0] + " C. ADR ULT CIERRE {0:.2f}".format(adr_ca) + " C. Loc ULT CIERRE {0:.2f}".format(local_ca))

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
        logging.debug(tickerlocal + " C. ADR: {0:.2f}".format(cotizadrf) + " C. Loc: {0:.2f}".format(cotizlocalf) + ' Fac.: ' + str(factor) + " CCL: {0:.2f}".format(resultado))
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
                        logging.warning("Lista de puntas incompleta. ")

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
        fecha = self.fecha
        threadvendedor = threading.Thread(target=self.worker_venta, name="HiloVentas")
        threadvendedor.start()
        logging.debug("Arranca larva: ")
        ###
        ### Bucle principal ##############################################################
        while (True):
            ahora = self.fecha.strftime('%d/%m/%Y %H:%M:%S')
            print("\tFecha: "+ahora)

            print(Fore.BLUE+"\nCompras: "+str(self.compras)+Fore.RESET)
            self.getTodasLasCotizaciones()
            enPeriodo = True

            now = datetime.now()
            minutosTranscurridos = (now - self.APERTURA).seconds / 60

            if (minutosTranscurridos <= self.PERIODOCOMPRA):
                logging.info(" Tiempo restante de compra: " + str(minutosTranscurridos))
                enPeriodo = True
            else:
                logging.info(" Ya no es periodo de compra.")
                print("Fin periodo de compra. ")
                enPeriodo = False


            for tt in self.lista:
                tickerlocal = tt[1].split(".")[0]
                local_up, precioCompra, cantidadCompra, punta_precioVenta, punta_cantidadVenta = self.getCotizacion(tickerlocal)

                valor_arbi = float(tt[5])
                cotizlocalf = float(local_up)
                cotizadrf = 0 #float(adr_up)

                diferencia = float(valor_arbi)-float(cotizlocalf)
                variacion = float((diferencia)*100)/float(cotizlocalf)

                if (variacion >= self.DIFPORCENTUALMINCOMPRA and enPeriodo):
                    ## Imprimo ticker con posibilidad de compra.
                    print(Fore.BLUE+tickerlocal + " => LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi) + " - VAR: {0:.2f}%".format(variacion)+Fore.RESET)
                    ##################
                    ### Proceso Compra
                    valorCompraMax, valorVentaMin = self.calculoValoresCompraYVenta(tickerlocal, cotizlocalf, valor_arbi)

                    if valorCompraMax != 0 and punta_precioVenta != 0 and valorCompraMax >= punta_precioVenta and not self.siExiste(self.compras, tickerlocal):
                        cantidad = self.MONTOCOMPRA // cotizlocalf
                        print(Fore.GREEN + " AVISO: Comprar: {0:.2f}".format(cantidad)+ " - Punta vendedora - Cant: {0:.2f}".format(
                            punta_cantidadVenta) + ", valor: {0:.2f}".format(punta_precioVenta) + Fore.RESET)
                        self.compra(tickerlocal, cotizlocalf, cantidad, valorVentaMin)
                else:
                    print(tickerlocal + " => LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi)+" - VAR: {0:.2f}%".format(variacion))
                    logging.info(tickerlocal + " * LOCAL: ${0:.2f}".format(cotizlocalf) + " - ARBITRADO: ${0:.2f}".format(valor_arbi)+" - VAR: {0:.2f}%".format(variacion))
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
        for campo in self.compras:
                if not campo[5]:
                    local_up, punta_precioCompra, punta_cantidadCompra, punta_precioVenta, punta_cantidadVenta = self.getCotizacion(campo[0])

                    ##Logica que tiene en cuenta el tipo que hace que esta comprado y cambia el ValorMinVenta
                    valorMinVenta = self.gradientePrecioVenta(campo)
                    campo[4] = valorMinVenta
                    self.actualizarCompras()

                    logging.info("Ticker: "+campo[0]+" Punta de compra: $ {0:.2f}".format(punta_precioCompra)+" Objetivo: $ {0:.2f}".format(valorMinVenta))

                    if punta_precioCompra !=0 and punta_precioCompra >= valorMinVenta:
                        print(Fore.BLUE+"\tObjetivo Venta CUMPLIDO: "+campo[0]+" Valor: {0:.2f}".format(punta_precioCompra)+Fore.RESET)
                        logging.info("Objetivo Venta CUMPLIDO: "+campo[0]+" Valor: {0:.2f}".format(punta_precioCompra))
                        if (punta_cantidadCompra < campo[2]):
                            logging.debug("La cantidad de la punta de compra es menor a la cantidad que se quiere vender. VER")

                        self.vender(campo[0], punta_precioCompra, campo[2])

    ## Orden que envia a Vender a IOL y agrega a la lista de operaciones pendientes.
    def vender(self, ticker, valor, cantidad):
        if not self.siExiste(self.ventas, ticker):
            logging.debug("Envio orden de VENTA: " + ticker + " Cantidad: {0:.2f}".format(
                cantidad) + " Valor: {0:.2f}".format(valor))
            self.agregarVenta(ticker, valor, cantidad)
            print(Fore.GREEN + "\tVenta Finalizada: " + ticker + " Valor: {0:.2f}".format(valor)+ " Cantidad: {0:.2f}".format(cantidad) + Fore.RESET)
        else:
            logging.debug("Esta venta ya fue hecha.")
        return 0

    ## En funcion del tiempo que hace que esta comprado el papel baja el valorMinVenta.
    ## compras ( TICKER, VALOR, CANTIDAD, NROOPERACION, VALORVENTAMIN, TIMESTAMP)

    def gradientePrecioVenta(self, campo):
        ahora = datetime.now()
        horarioCompra = campo[6]

        dif = ahora - datetime.strptime(horarioCompra,"%Y-%m-%d %H:%M:%S")
        valorCompra = campo[1]
        costoCompra = valorCompra + self.iol.calculoCostoOp(valorCompra)
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
        elif self.PERIODOVENTA <= ((ahora - self.APERTURA).seconds / 60):
            logging.info(campo[0] +
                         " Ejecuto Gradiente Final, Nuevo ValorVentaMin: ${0:.2f}".format(costoCompra))
            return costoCompra

        return campo[4]

    ## Calcula el punto medio entre el valor y el arbitrado y se mueve 0,5 para cada lado
    def calculoValoresCompraYVenta(self, ticker, valor, valorArbitrado):
        medio = (valorArbitrado + valor) / 2
        valorCompraMax = medio - (medio * (self.GANANCIAPORCENTUAL/2) / 100)
        valorVentaMin = medio + (medio * (self.GANANCIAPORCENTUAL/2) / 100)

        logging.debug(ticker+" COTIZ ACTUAL: $ {0:.2f}".format(valor)+"\t Valor compra Maximo {0:.2f}".format(valorCompraMax)+" -- Valor venta Minimo {0:.2f}".format(valorVentaMin))

        return [valorCompraMax, valorVentaMin]


    ## Orden que envia a comprar y agrega a la lista de operaciones pendientes.
    def compra(self, ticker, valor, cantidad, valorVentaMin):
            logging.debug("Envio orden de COMPRA: " + ticker + " Cantidad: {0:.2f}".format(
                cantidad) + " Valor: {0:.2f}".format(valor))
            self.agregarCompra(ticker, valor, cantidad, valorVentaMin)
            costoOperacion = self.iol.calculoCostoOp(valor)
            logging.info("Costo compra: {0:.2f}".format(costoOperacion))
            print("Comprado!!!")


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


    ## Calcula la cantidad a comprar.
    def calculoCantidad(self, ticker, precio):
        if precio==0: return 0
        return self.MONTOCOMPRA // precio

    ## Imprime el listado de compras hechas
    def printCompras(self):
        print(self.compras)

    def agregarCompra(self, ticker, valor, cantidad, valorVentaMin):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.compras.append([ticker, valor, cantidad, "000", valorVentaMin, False, ahora])
        self.actualizarVentas()


    def actualizarCompras(self):
        with open(self.PATH+"compras" + self.fecha.strftime('%d%m%Y') + ".dat", "wb") as f:
            pickle.dump(self.compras, f)
    
    def borrarCompras(self):
        l = []
        self.compras = l
        with open(self.PATH+"compras"+self.fecha.strftime('%d%m%Y')+".dat", "wb") as f:
            pickle.dump(self.compras, f)


    def agregarVenta(self, ticker, valor, cantidad):
        logging.debug("Agregando Venta Nueva")
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        campo = self.buscar(self.compras, ticker)
        if campo != None:
            campo[5] = True
            self.ventas.append([ticker, valor, cantidad, "000", ahora])
            self.actualizarVentas()

    def actualizarVentas(self):
        with open(self.PATH+"ventas" + self.fecha.strftime('%d%m%Y') + ".dat", "wb") as f:
            pickle.dump(self.ventas, f)

    def larvaBackTest(self, fecha):
        logging.info("Ejecutando Backtest.")

        logging.debug("Arranca larva: ")

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
                        cantidad = self.MONTOCOMPRA // cotizlocalf
                        print(Fore.GREEN +str(hora)+ " AVISO: Comprar: {0:.2f}".format(cantidad)+", valor: {0:.2f}".format(cotizlocalf) + Fore.RESET)
                        self.compra(ticker, cotizlocalf, cantidad, valorVentaMin)

                for campo in self.compras:
                    if not self.siExiste(self.ventas,ticker):
                        valorMinVenta = campo[4]
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
ahora = datetime.now()
a = AADR(lista, ahora)
a.larva()
