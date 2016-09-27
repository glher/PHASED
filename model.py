from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.models import BayesianModel

import timing


def phm_bn(bn_model, fname, cpd_w, phm_dat):
    weakness = 'Weakness %s' % fname
    detection = 'Detection %s' % fname
    corrective_action = 'Corrective Action %s' % fname
    failure = 'Failure %s' % fname

    bn_model.add_edges_from([(weakness, detection),
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
    phm_eff = phm_dat['Efficiency'][name]
    phm_err = phm_dat['Error'][name]
    phm_fck = phm_dat['Fuckup'][name]
    phm_rpr = phm_dat['Repair'][name]
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
    bn_model.add_cpds(cpd_w, cpd_d, cpd_c, cpd_f)
    # check_model checks for the network structure and CPDs and verifies that the CPDs are correctly
    # defined and sum to 1.
    bn_model.check_model()

    return bn_model


def get_cpd(parenting, val, gatetype):
    if len(parenting) > 1:
        if gatetype == 'and':
            cpd = [[1., 0.]] * (2 ** len(parenting) - 1) + [[val, 1 - val]]
        elif gatetype == 'or':
            cpd = [[1., 0.]] + [[val, 1 - val]] * (2 ** len(parenting) - 1)
        else:
            import sys
            sys.exit('Gate k/n not supported yet. Only OR and AND gates.')
        cpd = list(map(list, zip(*cpd)))
    else:
        cpd = [[1, val], [0., 1 - val]]
    return cpd


if __name__ == "__main__":

    # ################
    #      MODEL
    # ################
    nodes = ['Boundary input', 'Function 1', 'Function 2', 'Function 3', 'Function 10']
    connected_parents = {'Function 1': [['Boundary input']], 'Function 2': [['Function 1']],
                         'Function 3': [['Function 2']], 'Function 10': [['Function 2']]}
    # Probability that the function is weakened independently
    val_weak = {'Function 1': 0.04, 'Function 2': 0.032, 'Function 3': 0.0005,
                'Function 10': 0.02}
    # ################
    #       DATA
    # ################
    # Data from a database. Depends on the function and the phm sensors
    db_phm_on = {'Boundary input': False, 'Function 1': True, 'Function 2': False, 'Function 3': True,
                 'Function 10': True}
    # PHM off : Introduce 0. in corresponding db variables
    db_phm_eff = {'Boundary input': 0., 'Function 1': 0.95, 'Function 2': 0., 'Function 3': 0.98,
                  'Function 10': 0.995}
    db_phm_err = {'Boundary input': 0., 'Function 1': 0.01, 'Function 2': 0., 'Function 3': 0.001,
                  'Function 10': 0.02}
    db_phm_fck = {'Boundary input': 0., 'Function 1': 0.01, 'Function 2': 0., 'Function 3': 0.05,
                  'Function 10': 0.07}
    db_phm_rpr = {'Boundary input': 0., 'Function 1': 0.9, 'Function 2': 0., 'Function 3': 0.8,
                  'Function 10': 0.8}
    db_phm_dat = {'On': db_phm_on, 'Efficiency': db_phm_eff, 'Error': db_phm_err, 'Fuckup': db_phm_fck,
                  'Repair': db_phm_rpr}

    # ############
    #    BUILD
    # ############
    model = BayesianModel()
    for name in nodes:
        if not name == 'Boundary input':
            parents = ['Failure %s' % f for i in connected_parents[name] for f in i]  # If several: identify OR, AND, k/n
            for f in parents:
                model.add_edge(f, 'Weakness %s' % name)
            # AND:
            #  Always 2^len(upfail) - 1 values to give W(y), last value to give W(n)
            # OR:
            #  Always 1 value to give W(n), next 2^len(upfail) - 1 values to give W(y)
            # Okay-ish because binary, if 5 states, 5^len(upfail) can get really huge
            gate = 'and'
            cpdval = get_cpd(parents, val_weak[name], gate)
            cpd_weakness = TabularCPD(variable='Weakness %s' % name, variable_card=2, values=cpdval, evidence=parents,
                                      evidence_card=[2]*len(parents))
        else:
            cpd_weakness = TabularCPD(variable='Weakness %s' % name, variable_card=2, values=[[0.12, 0.88]])

        model = phm_bn(model, name, cpd_weakness, db_phm_dat)

    # #############
    #    RESULTS
    # #############
    # (0 = yes, 1 = no)
    infer = VariableElimination(model)
    print('Function 1\n\n')
    # print(infer.query(['Weakness Function 1'], evidence={'Weakness Function 1': 0, 'Weakness Function 2': 0})['Weakness Function 1'])
    print(infer.query(['Detection Function 1'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Detection Function 1'])
    print(infer.query(['Corrective Action Function 1'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Corrective Action Function 1'])
    print(infer.query(['Failure Function 1'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Failure Function 1'])
    print('\n\nFunction 2\n\n')
    # print(infer.query(['Weakness Function 2'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Weakness Function 2'])
    print(infer.query(['Detection Function 2'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Detection Function 2'])
    print(infer.query(['Corrective Action Function 2'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Corrective Action Function 2'])
    print(infer.query(['Failure Function 2'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Failure Function 2'])
    print('\n\nFunction 3\n\n')
    print(infer.query(['Weakness Function 3'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Weakness Function 3'])
    print(infer.query(['Detection Function 3'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Detection Function 3'])
    print(infer.query(['Corrective Action Function 3'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Corrective Action Function 3'])
    print(infer.query(['Failure Function 3'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Failure Function 3'])
    print('\n\nFunction 10\n\n')
    print(infer.query(['Weakness Function 10'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Weakness Function 10'])
    print(infer.query(['Detection Function 10'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Detection Function 10'])
    print(infer.query(['Corrective Action Function 10'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Corrective Action Function 10'])
    print(infer.query(['Failure Function 10'], evidence={'Failure Boundary input': 0, 'Weakness Function 2': 0})['Failure Function 10'])
