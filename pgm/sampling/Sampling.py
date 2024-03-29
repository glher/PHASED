import itertools
from collections import namedtuple

import networkx as nx
import numpy as np
from pandas import DataFrame
from pgm.extern.six.moves import map, range

from pgm.factors.discrete import factor_product
from pgm.inference import Inference
from pgm.models import BayesianModel, MarkovChain, MarkovModel
from pgm.utils.mathext import sample_discrete

State = namedtuple('State', ['var', 'state'])


class BayesianModelSampling(Inference):
    """
    Class for sampling methods specific to Bayesian Models

    Parameters
    ----------
    model: instance of BayesianModel
        model on which inference queries will be computed


    Public Methods
    --------------
    forward_sample(size)
    """
    def __init__(self, model):
        if not isinstance(model, BayesianModel):
            raise TypeError("Model expected type: BayesianModel, got type: ", type(model))

        self.topological_order = list(nx.topological_sort(model))
        super(BayesianModelSampling, self).__init__(model)

    def forward_sample(self, size=1):
        """
        Generates sample(s) from joint distribution of the bayesian network.

        Parameters
        ----------
        size: int
            size of sample to be generated

        Returns
        -------
        sampled: pandas.DataFrame
            the generated samples

        Examples
        --------
        >>> from pgm.models.BayesianModel import BayesianModel
        >>> from pgm.factors.discrete import TabularCPD
        >>> from pgm.sampling import BayesianModelSampling
        >>> student = BayesianModel([('diff', 'grade'), ('intel', 'grade')])
        >>> cpd_d = TabularCPD('diff', 2, [[0.6], [0.4]])
        >>> cpd_i = TabularCPD('intel', 2, [[0.7], [0.3]])
        >>> cpd_g = TabularCPD('grade', 3, [[0.3, 0.05, 0.9, 0.5], [0.4, 0.25,
        ...                0.08, 0.3], [0.3, 0.7, 0.02, 0.2]],
        ...                ['intel', 'diff'], [2, 2])
        >>> student.add_cpds(cpd_d, cpd_i, cpd_g)
        >>> inference = BayesianModelSampling(student)
        >>> inference.forward_sample(2)
                diff       intel       grade
        0        1           0          1
        1        1           0          2
        """
        sampled = DataFrame(index=range(size), columns=self.topological_order)
        for node in self.topological_order:
            cpd = self.model.get_cpds(node)
            states = range(self.cardinality[node])
            evidence = cpd.variables[:0:-1]
            if evidence:
                cached_values = self.pre_compute_reduce(variable=node)
                evidence = sampled.ix[:, evidence].values
                weights = list(map(lambda t: cached_values[tuple(t)], evidence))
            else:
                weights = cpd.values
            sampled[node] = sample_discrete(states, weights, size)
        return sampled

    def pre_compute_reduce(self, variable):
        variable_cpd = self.model.get_cpds(variable)
        variable_evid = variable_cpd.variables[:0:-1]
        cached_values = {}

        for state_combination in itertools.product(*[range(self.cardinality[var]) for var in variable_evid]):
            states = list(zip(variable_evid, state_combination))
            cached_values[state_combination] = variable_cpd.reduce(states, inplace=False).values

        return cached_values

    def rejection_sample(self, evidence=None, size=1):
        """
        Generates sample(s) from joint distribution of the bayesian network,
        given the evidence.

        Parameters
        ----------
        evidence: list of `pgm.factor.State` namedtuples
            None if no evidence
        size: int
            size of sample to be generated

        Returns
        -------
        sampled: pandas.DataFrame
            the generated samples

        Examples
        --------
        >>> from pgm.models.BayesianModel import BayesianModel
        >>> from pgm.factors.discrete import TabularCPD
        >>> from pgm.factors.discrete import State
        >>> from pgm.sampling import BayesianModelSampling
        >>> student = BayesianModel([('diff', 'grade'), ('intel', 'grade')])
        >>> cpd_d = TabularCPD('diff', 2, [[0.6], [0.4]])
        >>> cpd_i = TabularCPD('intel', 2, [[0.7], [0.3]])
        >>> cpd_g = TabularCPD('grade', 3, [[0.3, 0.05, 0.9, 0.5], [0.4, 0.25,
        ...                0.08, 0.3], [0.3, 0.7, 0.02, 0.2]],
        ...                ['intel', 'diff'], [2, 2])
        >>> student.add_cpds(cpd_d, cpd_i, cpd_g)
        >>> inference = BayesianModelSampling(student)
        >>> evidence = [State(var='diff', state=0)]
        >>> inference.rejection_sample(evidence, 2)
                intel       diff       grade
        0         0          0          1
        1         0          0          1
        """
        if evidence is None:
            return self.forward_sample(size)
        sampled = DataFrame(columns=self.topological_order)
        prob = 1
        while len(sampled) < size:
            _size = int(((size - len(sampled)) / prob) * 1.5)
            _sampled = self.forward_sample(_size)
            for evid in evidence:
                _sampled = _sampled[_sampled.ix[:, evid[0]] == evid[1]]
            prob = max(len(_sampled) / _size, 0.01)
            sampled = sampled.append(_sampled)
        sampled.reset_index(inplace=True, drop=True)
        return sampled[:size]

    def likelihood_weighted_sample(self, evidence=None, size=1):
        """
        Generates weighted sample(s) from joint distribution of the bayesian
        network, that comply with the given evidence.
        'Probabilistic Graphical Model Principles and Techniques', Koller and
        Friedman, Algorithm 12.2 pp 493.

        Parameters
        ----------
        evidence: list of `pgm.factor.State` namedtuples
            None if no evidence
        size: int
            size of sample to be generated

        Returns
        -------
        sampled: pandas.DataFrame
            the generated samples with corresponding weights

        Examples
        --------
        >>> from pgm.factors.discrete import State
        >>> from pgm.models.BayesianModel import BayesianModel
        >>> from pgm.factors.discrete import TabularCPD
        >>> from pgm.sampling import BayesianModelSampling
        >>> student = BayesianModel([('diff', 'grade'), ('intel', 'grade')])
        >>> cpd_d = TabularCPD('diff', 2, [[0.6], [0.4]])
        >>> cpd_i = TabularCPD('intel', 2, [[0.7], [0.3]])
        >>> cpd_g = TabularCPD('grade', 3, [[0.3, 0.05, 0.9, 0.5], [0.4, 0.25,
        ...         0.08, 0.3], [0.3, 0.7, 0.02, 0.2]],
        ...         ['intel', 'diff'], [2, 2])
        >>> student.add_cpds(cpd_d, cpd_i, cpd_g)
        >>> inference = BayesianModelSampling(student)
        >>> evidence = [State('diff', 0)]
        >>> inference.likelihood_weighted_sample(evidence, 2)
                intel       diff       grade  _weight
        0         0          0          1        0.6
        1         1          0          1        0.6
        """
        sampled = DataFrame(index=range(size), columns=self.topological_order)
        sampled['_weight'] = np.ones(size)
        evidence_dict = {var: st for var, st in evidence}
        for node in self.topological_order:
            cpd = self.model.get_cpds(node)
            states = range(self.cardinality[node])
            evidence = cpd.get_evidence()
            if evidence:
                evidence_values = sampled.ix[:, evidence].values
                cached_values = self.pre_compute_reduce(node)
                weights = list(map(lambda t: cached_values[tuple(t)], evidence_values))
                if node in evidence_dict:
                    sampled[node] = evidence_dict[node]
                    for i in range(size):
                        sampled.loc[i, '_weight'] *= weights[i][evidence_dict[node]]
                else:
                    sampled[node] = sample_discrete(states, weights)
            else:
                if node in evidence_dict:
                    sampled[node] = evidence_dict[node]
                    for i in range(size):
                        sampled.loc[i, '_weight'] *= cpd.values[evidence_dict[node]]
                else:
                    sampled[node] = sample_discrete(states, cpd.values, size)
        return sampled


class GibbsSampling(MarkovChain):
    """
    Class for performing Gibbs sampling.

    Parameters:
    -----------
    model: BayesianModel or MarkovModel
        Model from which variables are inherited and transition probabilites computed.

    Public Methods:
    ---------------
    set_start_state(state)
    sample(start_state, size)
    generate_sample(start_state, size)

    Examples:
    ---------
    Initialization from a BayesianModel object:
    >>> from pgm.factors.discrete import TabularCPD
    >>> from pgm.models import BayesianModel
    >>> intel_cpd = TabularCPD('intel', 2, [[0.7], [0.3]])
    >>> sat_cpd = TabularCPD('sat', 2, [[0.95, 0.2], [0.05, 0.8]], evidence=['intel'], evidence_card=[2])
    >>> student = BayesianModel()
    >>> student.add_nodes_from(['intel', 'sat'])
    >>> student.add_edge('intel', 'sat')
    >>> student.add_cpds(intel_cpd, sat_cpd)

    >>> from pgm.inference import GibbsSampling
    >>> gibbs_chain = GibbsSampling(student)

    Sample from it:
    >>> gibbs_chain.sample(size=3)
       intel  sat
    0      0    0
    1      0    0
    2      1    1
    """
    def __init__(self, model=None):
        super(GibbsSampling, self).__init__()
        if isinstance(model, BayesianModel):
            self._get_kernel_from_bayesian_model(model)
        elif isinstance(model, MarkovModel):
            self._get_kernel_from_markov_model(model)

    def _get_kernel_from_bayesian_model(self, model):
        """
        Computes the Gibbs transition models from a Bayesian Network.
        'Probabilistic Graphical Model Principles and Techniques', Koller and
        Friedman, Section 12.3.3 pp 512-513.

        Parameters:
        -----------
        model: BayesianModel
            The model from which probabilities will be computed.
        """
        self.variables = np.array(model.nodes())
        self.cardinalities = {var: model.get_cpds(var).variable_card for var in self.variables}

        for var in self.variables:
            other_vars = [v for v in self.variables if var != v]
            other_cards = [self.cardinalities[v] for v in other_vars]
            cpds = [cpd for cpd in model.cpds if var in cpd.scope()]
            prod_cpd = factor_product(*cpds)
            kernel = {}
            scope = set(prod_cpd.scope())
            for tup in itertools.product(*[range(card) for card in other_cards]):
                states = [State(v, s) for v, s in zip(other_vars, tup) if v in scope]
                prod_cpd_reduced = prod_cpd.reduce(states, inplace=False)
                kernel[tup] = prod_cpd_reduced.values / sum(prod_cpd_reduced.values)
            self.transition_models[var] = kernel

    def _get_kernel_from_markov_model(self, model):
        """
        Computes the Gibbs transition models from a Markov Network.
        'Probabilistic Graphical Model Principles and Techniques', Koller and
        Friedman, Section 12.3.3 pp 512-513.

        Parameters:
        -----------
        model: MarkovModel
            The model from which probabilities will be computed.
        """
        self.variables = np.array(model.nodes())
        factors_dict = {var: [] for var in self.variables}
        for factor in model.get_factors():
            for var in factor.scope():
                factors_dict[var].append(factor)

        # Take factor product
        factors_dict = {var: factor_product(*factors) if len(factors) > 1 else factors[0]
                        for var, factors in factors_dict.items()}
        self.cardinalities = {var: factors_dict[var].get_cardinality([var])[var] for var in self.variables}

        for var in self.variables:
            other_vars = [v for v in self.variables if var != v]
            other_cards = [self.cardinalities[v] for v in other_vars]
            kernel = {}
            factor = factors_dict[var]
            scope = set(factor.scope())
            for tup in itertools.product(*[range(card) for card in other_cards]):
                states = [State(var, s) for var, s in zip(other_vars, tup) if var in scope]
                reduced_factor = factor.reduce(states, inplace=False)
                kernel[tup] = reduced_factor.values / sum(reduced_factor.values)
            self.transition_models[var] = kernel

    def sample(self, start_state=None, size=1):
        """
        Sample from the Markov Chain.

        Parameters:
        -----------
        start_state: dict or array-like iterable
            Representing the starting states of the variables. If None is passed, a random start_state is chosen.
        size: int
            Number of samples to be generated.

        Return Type:
        ------------
        pandas.DataFrame

        Examples:
        ---------
        >>> from pgm.factors import DiscreteFactor
        >>> from pgm.inference import GibbsSampling
        >>> from pgm.models import MarkovModel
        >>> model = MarkovModel([('A', 'B'), ('C', 'B')])
        >>> factor_ab = DiscreteFactor(['A', 'B'], [2, 2], [1, 2, 3, 4])
        >>> factor_cb = DiscreteFactor(['C', 'B'], [2, 2], [5, 6, 7, 8])
        >>> model.add_factors(factor_ab, factor_cb)
        >>> gibbs = GibbsSampling(model)
        >>> gibbs.sample(size=4)
           A  B  C
        0  0  1  1
        1  1  0  0
        2  1  1  0
        3  1  1  1
        """
        if start_state is None and self.state is None:
            self.state = self.random_state()
        elif start_state is not None:
            self.set_start_state(start_state)

        sampled = DataFrame(index=range(size), columns=self.variables)
        sampled.loc[0] = [st for var, st in self.state]
        for i in range(size - 1):
            for j, (var, st) in enumerate(self.state):
                other_st = tuple(st for v, st in self.state if var != v)
                next_st = sample_discrete(list(range(self.cardinalities[var])),
                                          self.transition_models[var][other_st])[0]
                self.state[j] = State(var, next_st)
            sampled.loc[i + 1] = [st for var, st in self.state]
        return sampled

    def generate_sample(self, start_state=None, size=1):
        """
        Generator version of self.sample

        Return Type:
        ------------
        List of State namedtuples, representing the assignment to all variables of the model.

        Examples:
        ---------
        >>> from pgm.factors.discrete import DiscreteFactor
        >>> from pgm.sampling import GibbsSampling
        >>> from pgm.models import MarkovModel
        >>> model = MarkovModel([('A', 'B'), ('C', 'B')])
        >>> factor_ab = DiscreteFactor(['A', 'B'], [2, 2], [1, 2, 3, 4])
        >>> factor_cb = DiscreteFactor(['C', 'B'], [2, 2], [5, 6, 7, 8])
        >>> model.add_factors(factor_ab, factor_cb)
        >>> gibbs = GibbsSampling(model)
        >>> gen = gibbs.generate_sample(size=2)
        >>> [sample for sample in gen]
        [[State(var='C', state=1), State(var='B', state=1), State(var='A', state=0)],
         [State(var='C', state=0), State(var='B', state=1), State(var='A', state=1)]]
        """
        if start_state is None and self.state is None:
            self.state = self.random_state()
        else:
            self.set_start_state(start_state)

        for i in range(size):
            for j, (var, st) in enumerate(self.state):
                other_st = tuple(st for v, st in self.state if var != v)
                next_st = sample_discrete(list(range(self.cardinalities[var])),
                                          self.transition_models[var][other_st])[0]
                self.state[j] = State(var, next_st)
            yield self.state[:]
