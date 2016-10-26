import itertools
from collections import OrderedDict
from src.model import ModelData


class CombineSensors:
    def __init__(self, model_description):
        self.model_description = model_description
        self.exception_sensors = {'Boundary': '0', 'Gate': '0'}
        self.phm_file = 'dat/phm.yml'
        with open(self.phm_file, 'r') as yml:
            self.phm = ModelData.ordered_load(yml)
        self.truncation = True
        self.inventory = {'phm_1': 1, 'phm_2': 1, 'phm_3': 2, 'phm_4': 5}

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
            fm_class = self.model_description['classes'][self.model_description['nodes'][i]].split(' - ')[-1]
            #  Read in database to obtain the sensors that can be applied
            for p in self.phm:
                if fm_class in self.phm[p].keys():
                    specific_sensors.append(p)
            specific_sensors.append('0')
            phm_sensor_list.append(specific_sensors)
        return phm_sensor_list

    def potential_combinations(self, phm_sensor_list):

        phm_positions = OrderedDict(zip(self.model_description['nodes'], phm_sensor_list))
        maximum = 1
        for p in phm_positions:
            maximum *= len(phm_positions[p])
        print('Number of potential combinations: ', maximum)

    def inventory_combinations(self, states):
        inv_adj_states = []
        for i in states:
            respect = True
            combi_set = list(set(i))
            combi_set.remove('0')
            for s in combi_set:
                if i.count(s) > self.inventory[s]:
                    respect = False
            if respect:
                inv_adj_states.append(i)
        states = inv_adj_states

        print('Number of possible combinations: ', len(states))

        return states

    def truncation_combinations(self, states):
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
