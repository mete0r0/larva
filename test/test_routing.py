from unittest import TestCase
from routingorder import Estado, RoutingOrder
from datetime import datetime
from finance_dao import Iol
import logging
import logging.handlers
import os



class Routing(TestCase):
    ## LOGGER
    def loguear(self):
        # handler = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", "larva.log"))
        handler = logging.StreamHandler()
        formatter = logging.Formatter(' %(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s ')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
        root.addHandler(handler)

    def test_routing_venta(self):
        ventas = []
        ventas.append(["CRES", 48, 7, "000", Estado.ENPROCESO, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        r = Routing()

    def test_vender(self):
        iol = Iol()
        nro = iol.vender("CRES", 2, 48, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("Nro de operacion de venta: {}".format(nro))
        self.assertIsNotNone(nro)

    def test_borrar(self):
        iol = Iol()
        nro = iol.borrarOperacion("25146843")
        print("Respuesta al borrado: {}".format(nro))
        self.assertIsNotNone(nro)

    def test_getOperacion(self):
        iol = Iol()
        nro = iol.getOperacion("25259360")
        print("Respuesta al GetOperacion: {}".format(nro))
        self.assertIsNotNone(nro)

    def test_routing(self):
        self.loguear()
        compras =[]
        ventas =[]

        #compras.append(["CRES", 48.75, 1, "000", Estado.ENPROCESO, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        #ventas.append(["CRES", 49, 1, "000", Estado.ENPROCESO, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])


        r = RoutingOrder(compras, ventas, False)

        self.assertTrue(True)




