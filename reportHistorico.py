# -*- coding: utf-8 -*-
import pickle
from colorama import Fore
from finance_dao import Iol
from datetime import datetime, timedelta
import sys

i = 0
compras =[]
hoy = datetime.now()
#hoy = date(2020, 5, 19)
fechaFin = datetime.now()

if (len(sys.argv)==1):
    fechaInicio = hoy.strftime('%d%m%Y')

elif (len(sys.argv)==2):
    fechaInicio = sys.argv[1]
    fechaFin = datetime.now()

else:
    fechaInicio = sys.argv[1]
    fechaFin = sys.argv[2]

print("Rango Fechas: " + fechaInicio + " -- "+fechaFin +"\n")

fechaInicio = datetime.strptime(fechaInicio, '%d%m%Y')
fechaFin = datetime.strptime(fechaFin, '%d%m%Y')
difDias = (fechaFin - fechaInicio).days

for j in range(difDias):
    fechaa = fechaInicio + timedelta(days=j)
    fecha = fechaa.strftime('%d%m%Y')
    saldoTotal = 0
    saldoSinVender = 0
    compraTotalVendidos = 0

    print("Dia: " +fecha)
    try:
        with open("./data/compras"+fecha+ ".dat", "rb") as f:
            compras = pickle.load(f)
        print("Cantidad compras: " + str(len(compras)))
        print(compras)
    except:
        print("Dia: " + fecha + " Sin Compras.")


    try:
        ventas = []
        with open("./data/ventas"+fecha+ ".dat", "rb") as f:
            ventas = pickle.load(f)
        print("Cantidad ventas: " + str(len(ventas)))
        #print(ventas)
    except:
        print("Dia: " + fecha + " Sin Ventas.")


    compraTotal = float(0)
    compraTotalVendidos = float(0)
    saldoTotal = float(0)
    saldoSinVender = float(0)
    ventaTotal = float(0)
    vendio = False
    totalGanado = float(0)
    #iol = Iol()

    for c in compras:
        vendio = False
        for v in ventas:
            if c[0] == v[0]:
                comprado = float(c[2]*c[1])
                vendido = float(v[2]*v[1])
                compraTotal = compraTotal + comprado
                compraTotalVendidos = compraTotalVendidos + comprado
                ventaTotal = ventaTotal + vendido
                #print("\tCotiz compra: $ {0:.2f}".format(c[1])+" - Cotiz de venta: $ {0:.2f}".format(v[1]))
                costoCompra = (0.5*comprado/100)

                ganancia = vendido - (comprado+costoCompra)
                totalGanado = totalGanado + ganancia
                print(Fore.GREEN+"\tCerrada: "+c[0]+" GAN: $ {0:.2f}".format(float(ganancia))+", Fecha compra: "+str(c[6])+", Fecha Venta: "+str(v[4])+Fore.RESET)
                vendio = True

                break
        i +=1
        if not vendio:
            #print("\t Compra Abierta: "+ c[0]+ ", monto: {0:.2f} ".format(c[1]*c[2])+ " Objetivo: {0:.2f}".format(c[4]))
            compraTotal = compraTotal + float(c[1]*c[2])
            saldoSinVender = saldoSinVender + float(c[1]*c[2])
        #print(str(i)+"  "+c[0]+" Compra sin vender {0:.2f}".format(c[1])+" Time: "+ c[5])


    costoCompras = (0.5*compraTotal/100)
    saldoTotal = ventaTotal - (compraTotal+costoCompras)
    print(" Saldo: {0:.2f}".format(saldoTotal))
    print(" Saldo Sin vender: {0:.2f}".format(saldoSinVender))
    print(" Inversion total posiciones cerradas: {0:.2f}".format(compraTotalVendidos))
    if compraTotalVendidos != 0:
        print(" Ganado: {0:.2f}".format(totalGanado)+ " porcentaje: {0:.2f} %".format((totalGanado/(compraTotalVendidos))*100))

