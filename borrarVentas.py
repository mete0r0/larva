# -*- coding: utf-8 -*-
import pickle
l = []
with open("ventas.dat", "wb") as f:
    pickle.dump(l, f)


print("Ventas Borradas.")
