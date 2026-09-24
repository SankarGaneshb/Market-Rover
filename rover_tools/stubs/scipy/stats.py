"""Lightweight pure-python stats stub."""
import math

class NormDistribution:
    @staticmethod
    def cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @staticmethod
    def pdf(x):
        return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

norm = NormDistribution()
