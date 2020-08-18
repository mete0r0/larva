# -*- coding: utf-8 -*-
from finance_dao import Iol
import logging
import logging.handlers
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

    def __init__(self, compras, ventas, modotest, logger):
        self.compras = compras
        self.ventas = ventas
        self.modotest = modotest
        self.logging = logger
        self.logging.info("Iniciando RoutingOrder")


        th_operador_venta = threading.Thread(target=self.worker_operador_venta, name="Operador_Venta")
        th_operador_venta.start()

        th_operador_compra = threading.Thread(target=self.worker_operador_compra, name="Operador_Compra")
        th_operador_compra.start()

    def worker_operador_venta(self):
        self.logging.info("Iniciando operador de ventas")
        while (True):
            for venta in self.ventas:
                if (venta[4] == Estado.ENPROCESO):
                    self.logging.info("Ticker: {}, se envia orden de venta. ".format(venta[0]))
                    th_Vender = threading.Thread(target=self.worker_Vender, args=(venta,))
                    th_Vender.start()
                elif venta[4] == Estado.CURSANDO:
                    self.logging.info("Ticker: {}, se envia orden GetOperacion. ".format(venta[0]))
                    th_Vender = threading.Thread(target=self.worker_estado_op, args=(venta,))
                    th_Vender.start()
            print("VENTAS: "+ str(self.ventas))
            self.logging.info("Puleando Ventas, espero {}".format(self.TIMEREFRESH))
            time.sleep(self.TIMEREFRESH)

    def worker_Vender(self, venta):
        venta[4] = Estado.CURSANDO
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
            venta[3] = nroOrden
            self.logging.info("RUTEANDO operación de venta NRO ORDEN: {}".format(str(nroOrden)))

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

            self.logging.info("RUTEANDO GetOperacion {}, estado: {}".format(op[3],estadoActual))

    def worker_operador_compra(self):
        self.logging.info("Iniciando operador de compras")
        while (True):
            for compra in self.compras:
                if (compra[4] == Estado.ENPROCESO):
                    self.logging.info("Ticker: {}, se envia orden de compra. ".format(compra[0]))
                    th_Comprar = threading.Thread(target=self.worker_Comprar, args=(compra,))
                    th_Comprar.start()
                elif compra[4] == Estado.CURSANDO:
                    self.logging.info("Ticker: {}, se envia orden GetOperacion. ".format(compra[0]))
                    th_Comprar = threading.Thread(target=self.worker_estado_op, args=(compra,))
                    th_Comprar.start()

            print("COMPRAS: "+ str(self.compras))
            self.logging.info("Puleando Compras, espero {}".format(self.TIMEREFRESH))
            time.sleep(self.TIMEREFRESH)


    def worker_Comprar(self, compra):
        compra[4] = Estado.CURSANDO
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
            compra[3] = nroOrden
            self.logging.info("RUTEANDO operación de compra: NRO ORDEN: {}".format(str(nroOrden)))