from pgmpy.inference import VariableElimination


class Solver:

    def __init__(self, bayesian_model, display, evidence):
        self.evidence = evidence
        self.display = display
        self.bayesian_model = bayesian_model
        print(type(bayesian_model))
        self.inference = VariableElimination(self.bayesian_model)

    def get_inference(self, fname, fevidence):
        print('%s\n\n' % fname)
        if 'Gate' in fname:
            print(self.inference.query([fname], evidence=fevidence)[fname])
        else:
            for param in ['Weakness %s' % fname,
                          'Detection %s' % fname,
                          'Corrective Action %s' % fname,
                          'Failure %s' % fname]:
                if param in fevidence:
                    continue
                if fevidence:
                    print(self.inference.query([param], evidence=fevidence)[param])
                else:
                    print(self.inference.query([param])[param])
        print('\n\n')

    def run(self):
        # (0 = yes, 1 = no)
        for f in self.display:
            self.get_inference(f, self.evidence)
