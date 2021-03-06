from boat_sim.config.scenario_generator import generate_multi_scenario
from boat_sim.game import run_boat_experiments
from boat_sim.scripts.plot_results import ResultsManager, MultiTrialResults
import sys
import argparse



def parse_workflow(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', action='store', type=int, help='Number of boats.')
    parser.add_argument('--g', action='store_true', help='Generates scenario file with N boats (does not simulate).')
    parser.add_argument('--gsr', action='store_true', help='Generates and simulates scenario file'
                                                           ' with N boats, printing results.')
    parser.add_argument('--s', action='store_true', help='Runs scenario file with N boats and saves results.')
    parser.add_argument('--sr', action='store_true', help='Runs scenario file with N boats and plots results.')
    parser.add_argument('--r', action='store_true', help='Plots results from file.')
    parser.add_argument('--scenario', metavar='path', type=str, action='store', help='JSON file containing scenario.')
    parser.add_argument('--results', metavar='path', type=str, action='store', help='JSON file containing results.')
    args = parser.parse_args(args)

    ##############
    # GENERATION #
    ##############

    # If generate flags are on
    if args.g or args.gsr:
        # Generates scenario file.
        print("Generating scenario file...")
        # scenario_file = generate_random_scenario(args.n)
        scenario_file = generate_multi_scenario()
        print("Scenario file {} generated.".format(scenario_file))
    else:
        scenario_file = args.scenario

    ##############
    # SIMULATION #
    ##############

    if args.gsr or args.sr or args.s:
        print("Running simulation...")
        results_filename = run_boat_experiments(scenario_file)
        print("Results file {} generated.".format(results_filename))


    #############
    #  RESULTS  #
    #############

    if args.results:
        results_filename = args.results
        loader = ResultsManager(results_filename)
        loader.plot_results()
    elif args.gsr or args.sr:
        # loader = ResultsManager(results_filename)
        # loader.plot_results()
        loader = MultiTrialResults(g=40)


if __name__ == "__main__":
    parse_workflow(sys.argv[1:])


