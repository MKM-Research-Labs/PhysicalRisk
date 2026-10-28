# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""SEIS-001's credit, exactly, from its document (``seismic_resilience.pdf`` v0.10, s3).

With the generator's geometry R_JB is fixed, so the only random inputs to an
event's damage state are the magnitude M (truncated Gutenberg-Richter), the GMPE
residual and the fragility uniform. A single uniform against the nested fragility
curves gives P(DS >= i | PGA) = Phi((ln PGA - ln theta_i)/beta), and integrating
the lognormal residual out leaves P(DS >= i | M) = Phi((ln mu(M) + ln F_a -
ln theta_i) / sqrt(sigma^2 + beta^2)): one integral over M per damage state.
Losses are lognormals clipped to [0, 1] (Appendix E), whose means are closed
forms, and the post-earthquake-fire cascade takes the larger of two.
"""

import mpmath as mp

from config.models import ORACLE_REFERENCE_DPS, ORACLE_SEIS_EARTH_RADIUS_KM, ORACLE_SEIS_FAULT_LAT

DS = ("DS1", "DS2", "DS3")


def _phi(x):
    return mp.erfc(-x / mp.sqrt(2)) / 2


def r_jb(r_km, km_per_deg):
    """The generator places the asset r/km_per_deg degrees due south of the fault's
    midpoint; the clipped rupture always covers that foot, so R_JB is the
    great-circle distance to it."""
    dlat = mp.radians(mp.mpf(r_km) / km_per_deg)
    return 2 * ORACLE_SEIS_EARTH_RADIUS_KM * mp.asin(mp.sin(dlat / 2))


def site_class(vs30, gm):
    for cls, lower in sorted(gm.vs30_bands.items(), key=lambda kv: kv[1], reverse=True):
        if vs30 >= lower:
            return cls
    return min(gm.vs30_bands, key=gm.vs30_bands.get)  # pragma: no cover - the lowest band starts at 0


def theta(feat, cfg):
    """Model C (s3.4): the adjusted fragility medians and beta."""
    resp, frag = cfg.response, cfg.fragility
    has = set(feat["measures"])
    mult = {ds: mp.mpf(1) for ds in DS}
    for code, block in resp.measure_modifiers.items():
        if code in has:
            for ds in (DS if block["applies"] == "all" else [d for d in block["applies"] if d in DS]):
                mult[ds] *= 1 + mp.mpf(block["delta"])
    gov = resp.governance
    n = sum(code in has for code in gov["codes"])
    if n:
        for ds in DS:
            mult[ds] *= 1 + min(mp.mpf(gov["delta_each"]) * n, mp.mpf(gov["combined_cap"]))
    base = frag.medians_by_construction.get(feat["construction_type"]) or frag.medians_by_construction["Default"]
    return {ds: mp.mpf(base[ds]) * mult[ds] for ds in DS}, mp.mpf(base.get("beta", frag.default_beta))


def event_inputs(feat, cfg, km_per_deg):
    """The per-asset quantities the integrals need: zone, GMPE, sigma, F_a, R_JB, lambda."""
    occ, gm = cfg.occurrence, cfg.ground_motion
    zone = occ.hazard_class_to_zone.get(feat["seismic_hazard_class"], occ.default_zone)
    zb = occ.zones[zone]
    regime = zb.get("tectonic_regime", gm.default_regime)
    gmpe = gm.gmpe_by_regime.get(regime) or gm.gmpe_by_regime[gm.default_regime]
    cls = site_class(feat["soil_vs30_mps"], gm)
    amp = gm.soil_amplification
    fa = mp.mpf(amp["fa"]) if cls in amp["applies_classes"] and "GS02" not in feat["measures"] else mp.mpf(1)
    r = r_jb(feat["r_jb_km"], km_per_deg)
    fp = occ.fault_proximity
    m_fault = 1 + mp.mpf(fp["delta_gs01"]) if r < fp["threshold_km"] and "GS01" not in feat["measures"] else 1
    lam = mp.mpf(zb["lambda_zone"]) * m_fault * mp.mpf(occ.soil_recurrence_m_soil.get(cls, 1.0))
    return {"zone": zone, "b": mp.mpf(zb["b"]), "m_min": mp.mpf(zb["m_min"]), "m_max": mp.mpf(zb["m_max"]),
            "gmpe": gmpe, "sigma": mp.mpf(gmpe.get("sigma_total", gm.default_sigma_total)), "fa": fa,
            "r_jb": r, "vs30": mp.mpf(feat["soil_vs30_mps"]), "lam": lam, "site_class": cls}


def ln_median(m, r, vs30, g):
    """The GMPE median the code documents (groundmotion.py), with magnitude-dependent
    spreading; the model document gives no functional form."""
    dm = m - g["mref"]
    return (g["c0"] + g["c1"] * dm + g["c2"] * dm ** 2
            + (g["c3"] + g.get("c5", 0.0) * dm) * mp.log(mp.sqrt(r ** 2 + mp.mpf(g["h_km"]) ** 2))
            + g["c4"] * mp.log(vs30 / g["vref"]))


def gr_density(m, ev):
    b, lo, hi = ev["b"], ev["m_min"], ev["m_max"]
    return b * mp.log(10) * mp.power(10, -b * (m - lo)) / (1 - mp.power(10, -b * (hi - lo)))


def exceedance(ev, thetas, beta):
    """P(DS >= DS_i) per event, i = 1..3, integrated over the magnitude law."""
    s = mp.sqrt(ev["sigma"] ** 2 + beta ** 2)
    out = {}
    for ds in DS:
        f = lambda m: _phi((ln_median(m, ev["r_jb"], ev["vs30"], ev["gmpe"]) + mp.log(ev["fa"])
                            - mp.log(thetas[ds])) / s) * gr_density(m, ev)
        out[ds] = mp.quad(f, [ev["m_min"], ev["m_max"]])
    return out


def median_pga(ev):
    """The median of an event's PGA: G(x) = 1/2 with G the mixture CDF over M."""
    g = lambda x: mp.quad(lambda m: _phi((mp.log(x) - ln_median(m, ev["r_jb"], ev["vs30"], ev["gmpe"])
                                          - mp.log(ev["fa"])) / ev["sigma"]) * gr_density(m, ev),
                          [ev["m_min"], ev["m_max"]]) - mp.mpf(1) / 2
    lo = mp.exp(ln_median(ev["m_min"], ev["r_jb"], ev["vs30"], ev["gmpe"])) * ev["fa"]
    x = mp.findroot(g, (lo / 4, lo * 4), solver="anderson")
    h = x * mp.mpf(10) ** -12
    return x, (g(x + h) - g(x - h)) / (2 * h)               # the median and the density there


def clipped_mean(median, s):
    """E[min(X, 1)] for X lognormal with the given median and log-sd (clipped at 1)."""
    mu = mp.log(median)
    return mp.exp(mu + s ** 2 / 2) * _phi((-mu - s ** 2) / s) + _phi(mu / s)


def max_mean(m1, s1, m2, s2):
    """E[max(min(X1, 1), min(X2, 1))] for independent lognormals: int_0^1 1 - F1 F2."""
    cdf = lambda x, m, s: _phi((mp.log(x) - mp.log(m)) / s)
    return mp.quad(lambda x: 1 - cdf(x, m1, s1) * cdf(x, m2, s2), [0, mp.mpf(1) / 2, 1])


def clipped_second(median, s):
    """E[min(X, 1)^2] for X lognormal, as clipped_mean."""
    mu = mp.log(median)
    return mp.exp(2 * mu + 2 * s ** 2) * _phi((-mu - 2 * s ** 2) / s) + _phi(mu / s)


def max_second(m1, s1, m2, s2):
    cdf = lambda x, m, s: _phi((mp.log(x) - mp.log(m)) / s)
    return mp.quad(lambda x: 2 * x * (1 - cdf(x, m1, s1) * cdf(x, m2, s2)), [0, mp.mpf(1) / 2, 1])


def losses(cfg, has_gs15, moment=1):
    """E[L^moment | DS] for DS0..DS3 with the post-earthquake-fire cascade (s3.5, Appendix E)."""
    frag, pef = cfg.fragility, cfg.response.post_earthquake_fire
    lg = frag.loss_given_damage_state
    cfl = pef["conditional_fire_loss"]
    red = 1 - mp.mpf(pef["gs15_reduction"]) if has_gs15 else mp.mpf(1)
    out = {}
    for k in range(4):
        block, p = lg[f"DS{k}"], mp.mpf(pef["p_pef_by_ds"][f"DS{k}"]) * red
        if "fixed" in block:
            out[k] = mp.mpf(block["fixed"])
            continue
        one, both = (clipped_mean, max_mean) if moment == 1 else (clipped_second, max_second)
        s = one(mp.mpf(block["mean"]), mp.mpf(block["logstd"]))
        if k >= 2 and p > 0:
            s = (1 - p) * s + p * both(mp.mpf(block["mean"]), mp.mpf(block["logstd"]),
                                       mp.mpf(cfl["mean"]), mp.mpf(cfl["logstd"]))
        out[k] = s
    return out


def credit(feat, cfg, km_per_deg, with_median=False):
    """The resilience credit of s3.5, exactly."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        ev = event_inputs(feat, cfg, km_per_deg)
        thetas, beta = theta(feat, cfg)
        p = exceedance(ev, thetas, beta)
        ds_prob = [1 - p["DS1"], p["DS1"] - p["DS2"], p["DS2"] - p["DS3"], p["DS3"]]
        el = losses(cfg, "GS15" in feat["measures"])
        el2 = losses(cfg, "GS15" in feat["measures"], moment=2)
        q = -mp.expm1(-ev["lam"] * cfg.run.horizon_years)
        out = {"ev": ev, "thetas": thetas, "beta": beta, "p": p, "q": q,
               "no_collapse": 1 - p["DS3"],
               "loss": q * mp.fsum(ds_prob[k] * el[k] for k in range(4)),
               "loss_second": q * mp.fsum(ds_prob[k] * el2[k] for k in range(4)),
               "spread": q * p["DS3"] * cfg.run.loss_given_event_collapse}
        if with_median:
            out["pga"], out["pga_density"] = median_pga(ev)
        return out
