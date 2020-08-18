from AADR import AADR
from datetime import datetime


#PRODUCCION
lista=[]

ahora = datetime.now()
a = AADR(lista, ahora)
#a.compra('BMA',200, 20, 202)
#ti.sleep(5)
#a.vender(('BMA',280,1,"000", Estado.ENPROCESO, ahora), 300)
#a.agregarVenta("BMA", 300, 1)
a.larva()
