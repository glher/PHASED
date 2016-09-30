from src.bayesian import BayesianNetwork
from src.model import ModelData
from src.solver import Solver

if __name__ == "__main__":

    # Load the data
    model = ModelData()
    model_description = model.load()
    # Build the model
    bn = BayesianNetwork(model_description)
    bayesian_model = bn.build()
    # Solve the model
    evidence = {'Weakness Function 1': 0, 'Weakness Function 2': 0, 'Weakness Boundary input': 1}
    display = ['Boundary input',
               'Function 1',
               'Function 2',
               'Function 3',
               'Function 4',
               'Gate 1 f2-f4',
               'Function 10']
    solver = Solver(bayesian_model, display, evidence)
    solver.run()
