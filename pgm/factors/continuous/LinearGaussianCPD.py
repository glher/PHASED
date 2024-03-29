# -*- coding: utf-8 -*-

from __future__ import division

import numpy as np
from scipy.stats import multivariate_normal

from pgm.factors.continuous import ContinuousFactor


class LinearGaussianCPD(ContinuousFactor):
    u"""
    For, X -> Y the Linear Gaussian model assumes that the mean
    of Y is a linear function of mean of X and the variance of Y does
    not depend on X.

    For example,
    p(Y|X) = N(-2x + 0.9 ; 1)
    Here, x is the mean of the variable X.

    Let Y be a continuous variable with continuous parents
    X1 ............ Xk . We say that Y has a linear Gaussian CPD
    if there are parameters β0,.........βk and σ2 such that,

    p(Y |x1.......xk) = N(β0 + x1*β1 + ......... + xk*βk ; σ2)

    In vector notation,

    p(Y |x) = N(β0 + β.T * x ; σ2)

    """
    def __init__(self, variable, beta_0, variance, evidence=[], beta_vector=[]):
        """
        Parameters
        ----------

        variable: any hashable python object
            The variable whose CPD is defined.

        beta_0: int, float
            Represents the constant term in the linear equation.

        variance: int, float
            The variance of the variable defined.

        evidence: iterable of any hashabale python objects
            An iterable of the parents of the variable. None
            if there are no parents.

        beta_vector: iterable of int or float
            An iterable representing the coefficient vector of the linear equation.

        Examples
        --------

        # For P(Y| X1, X2, X3) = N(-2x1 + 3x2 + 7x3 + 0.2; 9.6)

        >>> cpd = LinearGaussianCPD('Y', 0.2, 9.6, ['X1', 'X2', 'X3'], [-2, 3, 7])
        >>> cpd.variable
        'Y'
        >>> cpd.variance
        9.6
        >>> cpd.evidence
        ['x1', 'x2', 'x3']
        >>> cpd.beta_vector
        [-2, 3, 7]
        >>> cpd.beta_0
        0.2

        """
        self.variable = variable
        self.beta_0 = beta_0
        self.variance = variance

        if len(evidence) != len(beta_vector):
            raise ValueError("The number of variables in evidence must be equal to the "
                             "length of the beta vector.")

        self.evidence = evidence
        self.beta_vector = np.asarray(beta_vector)

        variables = [variable] + evidence
        super(LinearGaussianCPD, self).__init__(variables, None)

    @property
    def pdf(self):

        def _pdf(*args):
            # The first element of args is the value of the variable on which CPD is defined
            # and the rest of the elements give the mean values of the parent variables.
            mean = sum([arg * coeff for (arg, coeff) in zip(args[1:], self.beta_vector)]) + self.beta_0
            return multivariate_normal.pdf(args[0], np.array(mean), np.array([[self.variance]]))

        return _pdf

    def copy(self):
        """
        Return a copy of the distribution.

        Returns
        -------
        LinearGaussianCPD: copy of the distribution

        Examples
        --------
        >>> from pgm.factors.continuous import LinearGaussianCPD
        >>> cpd = LinearGaussianCPD('Y', 0.2, 9.6, ['X1', 'X2', 'X3'], [-2, 3, 7])
        >>> copy_cpd = cpd.copy()
        >>> copy_cpd.variable
        'Y'
        >>> copy_cpd.evidence
        ['X1', 'X2', 'X3']
        """
        copy_cpd = LinearGaussianCPD(self.variable, self.beta_0, self.variance,
                                     list(self.evidence), self.beta_vector)

        return copy_cpd

    def __str__(self):
        if self.evidence and list(self.beta_vector):
            # P(Y| X1, X2, X3) = N(-2*X1_mu + 3*X2_mu + 7*X3_mu; 0.2)
            rep_str = "P(" + str(self.variable) + "| " + ", ".join([str(var) for var in self.evidence]) + ") = " +\
                      "N(" + " + ".join(["{coeff}*{parent}_mu".format(coeff=coeff, parent=parent)
                                        for coeff, parent in zip(self.beta_vector,
                                                                 self.evidence)]) + "; " + str(self.beta_0) + ")"
        else:
            # P(X) = N(1, 4)
            rep_str = "P({X}) = N({beta_0}; {variance})".format(X=str(self.variable), beta_0=str(self.beta_0),
                                                                variance=str(self.variance))
        return rep_str
