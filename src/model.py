import yaml
from collections import OrderedDict

class ModelData:

    def __init__(self):
        self.yml_file = 'dat/my_nodes_system_a.yml'
        with open(self.yml_file, 'r') as yml:
            self.system = self.ordered_load(yml)
        self.phm_file = 'dat/phm.yml'
        with open(self.phm_file, 'r') as yml:
            self.phm = self.ordered_load(yml)

    @staticmethod
    def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
        """
        Loads data from a yaml-file, ordered as read
        :param stream:
        :param Loader:
        :param object_pairs_hook:
        :return:
        """

        class OrderedLoader(Loader):
            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return yaml.load(stream, OrderedLoader)

    def load(self):
        # Load data from yml database. This "database" could be populated by a graphical interface - fault tree drawing.
        # Eventually, when the values are not given, it could be obtained from a database. Plus, see machine learning
        connected_parents = {}
        for k in self.system:
            if not self.system[k]['Parents']:
                continue
            elif not isinstance(self.system[k]['Parents'], list):
                connected_parents[k] = [self.system[k]['Parents']]
            else:
                connected_parents[k] = self.system[k]['Parents']
        nodes = [item for sublist in self.dep(connected_parents) for item in sublist]
        gate_parents = {}
        for k in self.system:
            if not self.system[k]['Gate']:
                gate_parents[k] = ''
                continue
            gate_parents[k] = self.system[k]['Gate'].lower()

        val_weak = {}
        for k in self.system:
            if not self.system[k]['Weakness']:
                continue
            val_weak[k] = float(self.system[k]['Weakness'])
        # ################
        #       DATA
        # ################
        # Data from a database. Depends on the function and the phm sensors

        db_phm_on = {}
        db_phm_eff = {}
        db_phm_err = {}
        db_phm_rpr = {}
        db_phm_fck = {}
        for k in self.system:
            if 'Gate' in k:
                continue
            if not self.system[k]['PHM']:
                db_phm_on[k] = False
                db_phm_eff[k] = 0.
                db_phm_err[k] = 0.
                db_phm_rpr[k] = 0.
                db_phm_fck[k] = 0.
                continue
            db_phm_on[k] = True
            sensor = self.system[k]['PHM']['sensor']
            db_phm_eff[k] = float(self.phm['PHM sensors'][sensor]['Efficiency'])
            db_phm_err[k] = float(self.phm['PHM sensors'][sensor]['Error rate'])
            db_phm_rpr[k] = float(self.system[k]['PHM']['repair'])
            db_phm_fck[k] = float(self.system[k]['PHM']['fuckup'])

        db_phm_dat = {'On': db_phm_on,
                      'Efficiency': db_phm_eff,
                      'Error': db_phm_err,
                      'Fuckup': db_phm_fck,
                      'Repair': db_phm_rpr}

        dict_model = {'nodes': nodes,
                      'connected parents': connected_parents,
                      'gate parents': gate_parents,
                      'value weakness': val_weak,
                      'database phm': db_phm_dat}
        return dict_model

    @staticmethod
    def dep(arg):
        """
            Dependency resolver

        "arg" is a dependency dictionary in which
        the values are the dependencies of their respective keys.
        """
        d = dict((k, set(arg[k])) for k in arg)
        r = []
        while d:
            # values not in keys (items without dep)
            t = set(i for v in d.values() for i in v) - set(d.keys())
            # and keys without value (items without dep)
            t.update(k for k, v in d.items() if not v)
            # can be done right away
            r.append(t)
            # and cleaned up
            d = dict(((k, v - t) for k, v in d.items() if v))
        return r
