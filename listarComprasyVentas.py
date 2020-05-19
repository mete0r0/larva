# -*- coding: utf-8 -*-
import pickle
l = []
with open("compras.dat", "wb") as f:
    pickle.dump(l, f)

print("Compras Borradas.")
