import numpy as np

G0 = 9.80665  # m/s^2 (standard gravity)
R = 287.05  # J/(kg·K) (gaz constant at sea level)
P0 = 101325.0  # Pa (air pressure at sea level)
T0 = 288.15  # K (temperature at sea level)


def pressure_ia(
    altitude_m,
    p0: float = P0,
    t0: float = T0,
    g0: float = G0,
    r: float = R,
):
    """Isothermal atmosphere : P(h) = P0 · exp( -g0 · h / (R · T0) )"""

    h = np.asarray(altitude_m, dtype=float)

    return p0 * np.exp(-g0 * h / (r * t0))
