# -*- coding: utf-8 -*-
import pickle
from datetime import datetime

l = []
hoy = datetime.now()

with open("compras"+hoy.strftime('%d%m%Y')+".dat", "wb") as f:
    pickle.dump(l, f)

print("Compras Borradas.")
