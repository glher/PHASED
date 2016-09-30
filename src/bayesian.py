from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import BayesianModel

import numpy as np
import sys


class BayesianNetwork:

    def __init__(self, dat):
        self.model = BayesianModel()
        self.dat = dat

    def build(self):
        for name in self.dat['nodes']:
            if 'Gate' in name:
                parents = ['Failure %s' % f if 'Gate' not in f else f for f in self.dat['connected parents'][name]]
                gate = self.dat['gate parents'][name]
                cpdval = self.get_cpd(len(parents), 0., gate)
                for f in parents:
                    self.model.add_edge(f, name)
                cpd_gate = TabularCPD(variable=name, variable_card=2, values=cpdval, evidence=parents,
                                      evidence_card=[2]*len(parents))
                self.model.add_cpds(cpd_gate)
            else:
                try:
                    parents = ['Failure %s' % f if 'Gate' not in f else f for f in self.dat['connected parents'][name]]
                    for f in parents:
                        self.model.add_edge(f, 'Weakness %s' % name)
                    gate = self.dat['gate parents'][name]
                    if len(parents) > 10:
                        sys.exit("%s: Too many parents (max: 10), not enough memory to deal with it without a smarter "
                                 "algorithm" % name)
                    cpdval = self.get_cpd(len(parents), self.dat['value weakness'][name], gate)
                    cpd_weakness = TabularCPD(variable='Weakness %s' % name, variable_card=2, values=cpdval,
                                              evidence=parents, evidence_card=[2]*len(parents))
                except KeyError:
                    cpd_weakness = TabularCPD(variable='Weakness %s' % name, variable_card=2, values=[[0.12, 0.88]])

                self.phm_bn(name, cpd_weakness, self.dat['database phm'])
        return self.model

    def phm_bn(self, fname, cpd_w, phm_dat):
        weakness = 'Weakness %s' % fname
        detection = 'Detection %s' % fname
        corrective_action = 'Corrective Action %s' % fname
        failure = 'Failure %s' % fname

        self.model.add_edges_from([(weakness, detection),
                                 (weakness, corrective_action),
                                 (weakness, failure),
                                 (detection, corrective_action),
                                 (corrective_action, failure)])
        # Detection: PHM detected an issue?
        # Real Signal: Was it a false positive?
        # Corrective Action Needed: Is a repair needed?
        # Corrective Action: Is the repair successful?
        # Failure: Failed or not?

        # Defining individual PHMs data.
        phm_eff = phm_dat['Efficiency'][fname]
        phm_err = phm_dat['Error'][fname]
        phm_fck = phm_dat['Fuckup'][fname]
        phm_rpr = phm_dat['Repair'][fname]
        # if not presence_phm:
        #     phm_eff = 0.
        #     phm_err = 0.

        # cpd_w = TabularCPD(variable=weakness, variable_card=2, values=[[0.004, 0.996]])

        cpd_d = TabularCPD(variable=detection, variable_card=2,
                           values=[[phm_eff, phm_err],
                                   [(1-phm_eff), (1-phm_err)]],
                           evidence=[weakness],
                           evidence_card=[2])

        # 0 or 1, action or not. This can be more nuanced, teams available, expertise, training, management, etc.
        # A detection might not automatically generate a corrective action.
        cpd_c = TabularCPD(variable=corrective_action, variable_card=2,
                           values=[[1., 0., 1., 0.],
                                   [0., 1., 0., 1.]],
                           evidence=[weakness, detection],
                           evidence_card=[2, 2])

        cpd_f = TabularCPD(variable=failure, variable_card=2,
                           values=[[1-phm_rpr, 1., phm_fck, 0.],
                                   [phm_rpr, 0., 1-phm_fck, 1.]],
                           evidence=[weakness, corrective_action],
                           evidence_card=[2, 2])

        # Associating the CPDs with the network
        self.model.add_cpds(cpd_w, cpd_d, cpd_c, cpd_f)
        # check_model checks for the network structure and CPDs and verifies that the CPDs are correctly
        # defined and sum to 1.
        self.model.check_model()

        return self.model

    @staticmethod
    def get_kofn_cpd(k, n, val):
        conditions = []
        cpd = []
        base = np.array([0, 1])
        for i in range(n):
            pattern = np.repeat(base, 2**i)
            conditions.append(list(pattern) * (2 ** (n-i-1)))
        conditions = [sum(i) for i in zip(*conditions)]
        for i, v in enumerate(conditions):
            if v < k:
                cpd.append([1., 0.])
            else:
                cpd.append([val, 1-val])
        return cpd

    def get_cpd(self, n, val, gatetype):
        if n > 1:
            if gatetype == 'and':
                cpd = self.get_kofn_cpd(n, n, val)
            elif gatetype == 'or':
                cpd = self.get_kofn_cpd(1, n, val)
            elif ' out of ' in gatetype:
                k = int(gatetype.split()[0])
                cpd = self.get_kofn_cpd(k, n, val)

            else:
                sys.exit('Gate not supported yet. Only OR, AND and KofN gates.')
            cpd = list(map(list, zip(*cpd)))
        else:
            cpd = [[1, val], [0., 1 - val]]
        return cpd
