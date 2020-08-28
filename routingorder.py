# -*- coding: utf-8 -*-
from finance_dao import Iol
import threading
from datetime import datetime
import time
from enum import Enum

class Estado(Enum):
    ENPROCESO = 1
    CURSANDO = 2
    CANCELADA = 3
    OPERADA = 4

class RoutingOrder(object):
    modotest = True
    compras = []  ##  ( TICKER, VALOR, CANTIDAD, NROOPERACION, Estado(Enum), TIMESTAMP, VALORVENTAMIN)
    ventas = []  ##   ( TICKER, VALOR, CANTIDAD, NROOPERACION, Estado(Enum), TIMESTAMP)
    TIMEREFRESH = 1
    FINCOMPRA = False
    enPeriodoCompra = False

    def __init__(self, compras, ventas, modotest, logger, enPeriodoCompra):
        self.compras = compras
        self.ventas = ventas
        self.modotest = modotest
        self.logging = logger
        self.logging.info("Iniciando RoutingOrder")
        self.enPeriodoCompra = enPeriodoCompra

        th_operador_venta = threading.Thread(target=self.worker_operador_venta, name="Operador_Venta")
        th_operador_venta.start()

        th_operador_compra = threading.Thread(target=self.worker_operador_compra, name="Operador_Compra")
        th_operador_compra.start()

    ###
    def worker_operador_venta(self):
        self.logging.info("Iniciando operador de ventas")
        hayPendiente = False

        while (True):
            for venta in self.ventas:
                if (venta[4] == Estado.ENPROCESO):
                    self.logging.info("Ticker: {}, se envia orden de venta. ".format(venta[0]))
                    th_Vender = threading.Thread(target=self.worker_Vender, args=(venta,))
                    th_Vender.start()
                    hayPendiente = True

                elif venta[4] == Estado.CURSANDO:
                    self.logging.info("Ticker: {}, se envia orden GetOperacion # ".format(venta[0], venta[3]))
                    th_Vender = threading.Thread(target=self.worker_estado_op, args=(venta,))
                    th_Vender.start()
                    hayPendiente = True
                elif venta[4] != Estado.OPERADA:
                    hayPendiente = True
                    self.logging.info("Estado de la orden")
            if not hayPendiente and self.FINCOMPRA:
                self.logging.info("Fin hilo operador Ventas")
                return 0

            print("VENTAS: "+ str(self.ventas))
            self.logging.info("Puleando Ventas, espero {}".format(self.TIMEREFRESH))
            time.sleep(self.TIMEREFRESH)
    ###
    def worker_Vender(self, venta):
        ticker = venta[0]
        cantidad = venta[2]
        precio = venta[1]
        validez = datetime.now().strftime('%Y-%m-%d')

        if self.modotest:
            self.logging.info(" Vendiendo en modo test.")
            time.sleep(self.TIMEREFRESH)
            venta[4] = Estado.OPERADA
        else:
            iol = Iol()
            nroOrden = iol.vender(ticker, cantidad, precio, validez)
            if (nroOrden != "000"):
                venta[3] = nroOrden
                venta[4] = Estado.CURSANDO
                self.logging.info("RUTEANDO operación de venta NRO ORDEN: {}".format(str(nroOrden)))
            else:
                self.logging.info("La operacion de venta {}, no fue recibida por el broker".format(venta[0]))

    ## Recupera del broker el estado de la operación
    def worker_estado_op(self, op):
        if self.modotest:
            time.sleep(12)
            op[4] = Estado.OPERADA
        else:
            iol = Iol()
            estadoActual = iol.getOperacion(op[3])
            if estadoActual == "terminada":
                op[4] = Estado.OPERADA
            elif estadoActual == "cancelada":
                op[3] = "000"
                op[4] = Estado.ENPROCESO
            else:
                self.logging.info("Orden {} en estado {} ".format(op[3],op[4]))

            self.logging.info("RUTEANDO GetOperacion # {}, estado: {}".format(op[3], estadoActual))

    ##
    def worker_operador_compra(self):
        self.logging.info("Iniciando operador de compras")
        while (True):
            hayPendiente = False

            for compra in self.compras:
                if (compra[4] == Estado.ENPROCESO):
                    self.logging.info("Ticker: {}, se envia orden de compra. ".format(compra[0]))
                    th_Comprar = threading.Thread(target=self.worker_Comprar, args=(compra,))
                    th_Comprar.start()
                    hayPendiente = True
                elif compra[4] == Estado.CURSANDO:
                    self.logging.info("Ticker: {}, se envia orden GetOperacion. # {} ".format(compra[0], compra[3]))
                    th_Comprar = threading.Thread(target=self.worker_estado_op, args=(compra,))
                    th_Comprar.start()
                    hayPendiente = True
                elif compra[4] != Estado.OPERADA:
                    hayPendiente = True
                    self.logging.info("No al compras pendientes de orden.")
            if not hayPendiente and not self.enPeriodoCompra:
                self.FINCOMPRA = True
                self.logging.info("Fin hilo operador Compra")

                return 0

            print("COMPRAS: "+ str(self.compras))
            self.logging.info("Puleando Compras, espero {}".format(self.TIMEREFRESH))
            time.sleep(self.TIMEREFRESH)
    ##
    def worker_Comprar(self, compra):
        ticker = compra[0]
        cantidad = compra[2]
        precio = compra[1]
        validez = datetime.now().strftime('%Y-%m-%d')

        if self.modotest:
            self.logging.info(" Comprando en modo test.")
            time.sleep(3)
            compra[4] = Estado.OPERADA
        else:
            iol = Iol()
            nroOrden = iol.comprar(ticker, cantidad, precio, validez)
            if (nroOrden != "000"):
                compra[3] = nroOrden
                compra[4] = Estado.CURSANDO
                self.logging.info("RUTEANDO operación de compra: NRO ORDEN: {}".format(str(nroOrden)))
            else:
                self.logging.info("La operacion de compra {}, no fue recibida por el broker".format(compra[0]))
