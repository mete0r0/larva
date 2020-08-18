# -*- coding: utf-8 -*-
import pickle
import logging


class Dao:
    def __init__(self, PATH):
        self.PATH = PATH

    def save(self, lista, nombreArch, fecha):
        with open(self.PATH + "data/"+nombreArch + fecha.strftime('%d%m%Y') + ".dat", "wb") as f:
            pickle.dump(lista, f)

    def load(self, lista, nombreArch, fecha):
        try:
            with open(self.PATH + "data/"+nombreArch+fecha.strftime('%d%m%Y') + ".dat", "rb") as f:
                lista = pickle.load(f)
        except Exception:
            pickle.dump(lista, open(self.PATH + "data/"+nombreArch + fecha.strftime('%d%m%Y') + ".dat", "wb"))

    def actualizarCompras(self, compras, fecha):
        with open(self.PATH + "data/compras" + fecha.strftime('%d%m%Y') + ".dat", "wb") as f:
            pickle.dump(compras, f)

    def actualizarVentas(self, ventas, fecha):
        with open(self.PATH + "data/ventas" + fecha.strftime('%d%m%Y') + ".dat", "wb") as f:
            pickle.dump(ventas, f)

    def borrarCompras(self):
        l = []
        self.compras = l
        with open(self.PATH + "data/compras" + self.fecha.strftime('%d%m%Y') + ".dat", "wb") as f:
            pickle.dump(self.compras, f)

    ## Carga las listas de compras y ventas desde archivo.
    def getComprasVentasfromFile(self, compras, ventas, fecha, iol):
        ##Cargo compras desde archivo
        try:
            with open(self.PATH + "data/compras" + fecha.strftime('%d%m%Y') + ".dat", "rb") as f:
                compras = pickle.load(f)
        except Exception:
            pickle.dump(compras, open(self.PATH + "data/compras" + fecha.strftime('%d%m%Y') + ".dat", "wb"))

        print("Cantidad compras en Inicio: " + str(len(compras)))
        print(compras)

        ##Cargo ventas desde archivo
        try:
            with open(self.PATH + "data/ventas" + fecha.strftime('%d%m%Y') + ".dat", "rb") as f:
                ventas = pickle.load(f)
        except Exception:
            pickle.dump(ventas, open(self.PATH + "data/ventas" + fecha.strftime('%d%m%Y') + ".dat", "wb"))

        print("Cantidad ventas en Inicio: " + str(len(ventas)))
        print(ventas)

        compraTotal = 0
        ventaTotal = 0

        gan = 0

        for c in compras:
            for v in ventas:
                if c[0] == v[0]:
                    comprado = float(c[2] * c[1])
                    vendido = float(v[2] * v[1])
                    compraTotal = compraTotal + comprado
                    ventaTotal = ventaTotal + vendido
                    costoCompra = iol.calculoCostoOp(comprado)
                    costoVenta = iol.calculoCostoOp(vendido)
                    ganancia = (vendido + costoVenta) - (comprado + costoCompra)
                    gan = gan + ganancia
                    break
        logging.info(" *** Ganancia: ${0:.2f} ***".format(gan))

