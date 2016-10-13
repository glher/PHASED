import sys

from pgm.inference import VariableElimination


class Solver:

    def __init__(self, bayesian_model, display, evidence):
        self.evidence = evidence
        self.display = display
        self.bayesian_model = bayesian_model
        self.inference = VariableElimination(self.bayesian_model)

    def get_inference(self, fname, score):
        # print('%s\n\n' % fname)
        if 'Gate' in fname:
            # print(self.inference.query([fname], evidence=self.evidence)[fname])
            pass
        else:
            for param in [#'Weakness %s' % fname,
                          #'Detection %s' % fname,
                          #'Corrective Action %s' % fname,
                          'Failure %s' % fname]:
                if param in self.evidence:
                    continue
                if self.evidence:
                    score += self.inference.query([param], evidence=self.evidence)[param].values[0]
                else:
                    score += self.inference.query([param])[param].values[0]
        return score

    def get_map_param(self, fname, param):
        if 'Gate' in fname:
            if fname not in self.evidence:
                param.append(fname)
        else:
            for p in ['Weakness %s' % fname,
                      'Detection %s' % fname,
                      'Corrective Action %s' % fname,
                      'Failure %s' % fname]:
                if p not in self.evidence:
                    param.append(p)
        return param

    def run(self, mapquery=False):
        # (0 = yes, 1 = no)
        param = []
        score = 0.
        for f in self.display:
            if not mapquery:
                score += self.get_inference(f, score)
            else:
                param = self.get_map_param(f, param)
        if mapquery:
            print(len(param))
            if len(param) > 20:
                sys.exit("Potential memory overload. Abort.")
            print(self.inference.map_query(param, evidence=self.evidence))
        return score
