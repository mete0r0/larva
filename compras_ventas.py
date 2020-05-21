# -*- coding: utf-8 -*-
import pickle
from colorama import Fore

i = 0
compras =[]
with open("compras.dat", "rb") as f:
    compras = pickle.load(f)
print("Cantidad compras: " + str(len(compras)))
print(compras)

ventas = []
with open("ventas.dat", "rb") as f:
    ventas = pickle.load(f)
print("Cantidad ventas: " + str(len(ventas)))
#print(ventas)

for c in compras:
    for v in ventas:
        if c[0] == v[0]:
            comprado = float(c[2]*c[1])
            vendido = float(v[2]*v[1])
            print("\tCotiz compra: $ {0:.2f}".format(c[1]))
            print(Fore.GREEN+"\tCerrada: "+c[0]+" GAN: $ {0:.2f}".format(float(vendido-comprado))+", Fecha compra: "+str(c[5])+", Fecha Venta: "+str(v[4])+Fore.RESET)
            break
    i +=1
    #print(str(i)+"  "+c[0]+" Compra sin vender {0:.2f}".format(c[1])+" Time: "+ c[5])


