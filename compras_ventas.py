# -*- coding: utf-8 -*-
import pickle

compras =[]
with open("compras.dat", "rb") as f:
    compras = pickle.load(f)
print("Cantidad compras: " + str(len(compras)))
print(compras+"\n\n")

ventas = []
with open("ventas.dat", "rb") as f:
    ventas = pickle.load(f)
print("Cantidad ventas: " + str(len(ventas)))
print(ventas+"\n\n")


