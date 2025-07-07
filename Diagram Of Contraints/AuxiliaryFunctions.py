import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def ConstraintPoly(WSl, TWl, Col, al):
    W = WSl.copy()
    T = TWl.copy()
    W.append(W[-1])
    T.append(0)
    W.append(W[0])
    T.append(0)
    W.append(0)
    T.append(T[-2])
    zp = list(zip(W, T))
    pa = Polygon(zp, closed=True, color=Col, alpha=al)
    return pa

