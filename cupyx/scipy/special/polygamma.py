import cupy
from cupyx.scipy import special


def polygamma(n, x):
    """Polygamma function n.

    .. seealso:: :data:`scipy.special.polygamma`

    """
    n, x = cupy.asarray(n), cupy.asarray(x)
    n, x = cupy.broadcast_arrays(n, x)
    fac2 = (-1.0)**(n+1) * special.gamma(n+1.0) * special.zeta(n+1.0, x)
    return cupy.where(n == 0, special.digamma(x), fac2)
