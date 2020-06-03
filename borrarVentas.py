# -*- coding: utf-8 -*-
import pickle
from datetime import datetime

l = []
hoy = datetime.now()


with open("ventas"+hoy.strftime('%d%m%Y')+".dat", "wb") as f:
    pickle.dump(l, f)


print("Ventas Borradas.")
