#!/bin/bash
HOY=$(date +%Y-%m-%d)
cp /usr/src/larva/compras.dat /usr/src/larva/operacionesViejas/compras_$HOY.dat

cp /usr/src/larva/ventas.dat /usr/src/larva/operacionesViejas/ventas_$HOY.dat


python /usr/src/larva/borrarCompras.py
python /usr/src/larva/borrarVentas.py



