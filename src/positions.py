import itertools
from collections import OrderedDict, defaultdict
from src.model import ModelData


class CombineSensors:
    def __init__(self, model_description):
        self.model_description = model_description
        self.exception_sensors = {'Boundary': '0', 'Gate': '0'}
        self.phm_file = 'dat/phm.yml'
        with open(self.phm_file, 'r') as yml:
            self.phm = ModelData.ordered_load(yml)
        self.truncation = True
        self.inventory = {'phm_1': 0, 'phm_2': 0, 'phm_3': 0, 'phm_4': 0, '0': len(self.model_description['nodes'])}

    def run(self):
        phm_sensor_list = self.get_system_sensors()
        self.potential_combinations(phm_sensor_list)
        states = itertools.product(*phm_sensor_list)
        states = self.inventory_combinations(states)
        if self.truncation:
            states = self.truncation_combinations(states)
        return states

    def get_system_sensors(self):
        phm_sensor_list = []
        for i, n in enumerate(self.model_description['nodes']):
            specific_sensors = []
            exception = False
            for e in self.exception_sensors:
                if e in n:
                    specific_sensors.append(self.exception_sensors[e])
                    phm_sensor_list.append(specific_sensors)
                    exception = True
                    break
            if exception:
                continue
            fm_class = self.model_description['classes'][self.model_description['nodes'][i]].split(' - ')
            #  Read in database to obtain the sensors that can be applied
            available_phm = [p for p in self.inventory if self.inventory[p] > 0 and p != '0']
            for p in available_phm:
                for cat in reversed(fm_class):
                    if cat in self.phm[p].keys():
                        specific_sensors.append(p)
                        break
            if self.truncation:
                if not specific_sensors:
                    specific_sensors.append('0')
            else:
                specific_sensors.append('0')
            phm_sensor_list.append(specific_sensors)
        return phm_sensor_list

    def potential_combinations(self, phm_sensor_list):

        phm_positions = OrderedDict(zip(self.model_description['nodes'], phm_sensor_list))
        maximum = 1
        for p in phm_positions:
            maximum *= len(phm_positions[p])
        print('Number of minimum combinations: ', maximum)

    def inventory_combinations(self, states):
        all_states = []
        for state in states:
            dups = defaultdict(list)
            for i, e in enumerate(state):
                dups[e].append(i)

            potential = OrderedDict()
            for k, v in sorted(iter(dups.items())):
                potential[k] = []
                for i in itertools.combinations(v, self.inventory[k]):
                    potential[k].append(i)
                if not potential[k]:
                    potential[k].append(tuple(v))

            combiset = [potential[i] for i in potential]
            sensors = [k for k in potential]
            for combi in itertools.product(*combiset):
                final = ['0'] * len(state)
                for j, v in enumerate(combi):
                    for s in v:
                        final[s] = sensors[j]
                all_states.append(final)
        states = all_states
        print('Number of possible combinations: ', len(states))
        return states

    @staticmethod
    def truncation_combinations(states):
        """
        The truncation selects the combinations containing the maximum number of PHM sensors available. All the
        functions and flows that can be equipped with a sensor are.
        :param states:
        :return:
        """
        min_zeros = len(states[0])
        for i in states:
            if i.count('0') < min_zeros:
                min_zeros = i.count('0')
        trunc_states = []
        for i in states:
            trunc = False
            if i.count('0') > min_zeros:
                trunc = True
            if not trunc:
                trunc_states.append(i)
        states = trunc_states

        print('Number of truncated combinations: ', len(states))
        if len(states) > 1000:
            print('It will take a long time')
        return states
