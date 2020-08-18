from unittest import TestCase
from AADR import AADR
from datetime import datetime
from dao import Dao


class testingGral(TestCase):

    def test_completo(self):
        lista = []
        ahora = datetime.now()
        a = AADR(lista, ahora)
        #def compra(self, ticker, valor, cantidad, valorVentaMin):
        a.compra('BMA', 280, 1, 300)
        a.larva()

    def test_dao(self):
        lista = []
        lista.append([1,2,3,4])
        dao = Dao("/Users/MeteOro/codigo/larva/")
        ahora = datetime.now()


        dao.save(lista, "prueba", ahora)