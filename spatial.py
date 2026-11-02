import math
BASKET_Y=1.575
def normalize_euroleague(x_raw,y_raw):
    if 0<=x_raw<=1500: x=x_raw/100-7.5
    elif -750<=x_raw<=750: x=x_raw/100
    else: raise ValueError("unsupported x coordinate")
    return max(-7.5,min(7.5,x)),max(0,min(14,y_raw/100))
def normalize_acb(x_pct,y_pct): return (x_pct/100)*15-7.5,(y_pct/100)*14
def normalize_bcl(x_m,y_m): return max(-7.5,min(7.5,x_m)),max(0,min(14,y_m))
def normalize_lba(x_norm,y_norm): return x_norm*15-7.5,y_norm*14
def shot_distance(x,y): return math.sqrt(x*x+(y-BASKET_Y)**2)
def classify_shot_zone(x,y):
    r=shot_distance(x,y)
    if r<=1.25 and y>=BASKET_Y:return "RESTRICTED_AREA"
    if abs(x)<=2.45 and y<=5.80:return "PAINT_NON_RA"
    if x<=-6.60 and y<=2.99:return "CORNER_3_LEFT"
    if x>=6.60 and y<=2.99:return "CORNER_3_RIGHT"
    if r>=6.75 and y>2.99:return "ABOVE_THE_BREAK_3"
    if x<-2.45 and r<6.75:return "MID_RANGE_LEFT"
    if x>2.45 and r<6.75:return "MID_RANGE_RIGHT"
    return "MID_RANGE_CENTER"
