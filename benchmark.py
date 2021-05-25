from agent_queue import *
from boat_culture import *
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time
import csv
from datetime import datetime
from itertools import *
import numpy as np

RANDOM_SAMPLES = 1


def run_test(base_queue, baseline, privacy_budget, arg_strategy, test_type='ordering'):
    if test_type == 'ordering':
        return run_test_ordering(base_queue, baseline, privacy_budget, arg_strategy)
    elif test_type == 'matrix':
        return run_test_matrix(base_queue, baseline, privacy_budget, arg_strategy)


def run_test_ordering(base_queue, baseline, privacy_budget, arg_strategy):
    averaged_tau = 0
    averaged_unfairness = 0
    # for i in range(num_samples):
    q = copy.deepcopy(base_queue)
    q.set_privacy_budget(privacy_budget)
    q.set_strategy(arg_strategy)
    swaps = q.interact_all()
    text, tau, p = q.relative_queue(ground_truth=baseline)
    if arg_strategy == ArgStrategy.LEAST_ATTACKERS_PRIVATE:
        print("\nLeast. queue: {}".format(text))
        print("Swaps: {}".format(swaps))
        print("Tau: {}".format(tau))
    elif arg_strategy == ArgStrategy.MOST_ATTACKS_PRIVATE:
        print("\nMost. queue: {}".format(text))
        print("Swaps: {}".format(swaps))
        print("Tau: {}".format(tau))
    elif arg_strategy == ArgStrategy.RANDOM_CHOICE_PRIVATE:
        print("\nRandom queue: {}".format(text))
        print("Swaps: {}".format(swaps))
        print("Tau: {}".format(tau))
    averaged_tau += tau
    averaged_unfairness += q.rate_local_unfairness
    return averaged_tau, averaged_unfairness


def dag_distance(aq: AgentQueue, ground_truth, result, p, q):
    # Let's consider only determined relationships as edges.
    edges_gtr = []
    edges_res = []

    a = 0
    b = 0
    c = 0

    distance = 0
    total_pairs = 0
    for i in range(0, len(aq.queue) - 1):
        for j in range(i, len(aq.queue)):
            if i == j:
                continue
            total_pairs += 1
            pair = (i, j)
            riap = (j, i)

            edge_in_gt = False
            edge_in_res = False
            if ground_truth[pair] == ground_truth[riap]:
                edges_gtr.append((i, j) if ground_truth[pair] == i else (j, i))
                edge_in_gt = True
            if result[pair] == result[riap]:
                edges_res.append((i, j) if result[pair] == i else (j, i))
                edge_in_res = True

            # Case 1: do nothing, distance starts as 0 anyway

            # Case 2: reversed case, max distance
            if ((pair in edges_gtr) and (riap in edges_res)) \
                    or \
                    ((riap in edges_gtr) and (pair in edges_res)):
                c += 1
            # Case 3: edge only exists in one case
            elif (edge_in_gt and not edge_in_res) or (edge_in_res and not edge_in_gt):
                a += 1
            # Case 4: no edge in either
            elif (not edge_in_gt) and (not edge_in_res):
                b += 1

    return (a, b, c, total_pairs)


def compare_results(baseline, target):
    match = 0
    total = 0
    for pair, winner in baseline.items():
        if baseline[pair] == target[pair]:
            match += 1
        total += 1
    return match / total


def run_test_matrix(base_queue, ground_truth_matrix, privacy_budget, arg_strategy):
    q = copy.deepcopy(base_queue)
    q.set_privacy_budget(privacy_budget)
    q.set_strategy(arg_strategy)
    winners = q.interact_all_matrix()
    a, b, c, total_pairs = dag_distance(q, ground_truth_matrix, winners, p=0, q=0)
    queue_data = q.results_to_dict()
    # print("{}\nDistance: {}".format(arg_strategy, result))
    return a, b, c, total_pairs, q.rate_local_unfairness, queue_data


def benchmark_same_strategy(num_experiments, queue_size, max_privacy_budget, test_type='ordering'):
    t0 = time.time()
    i = 0
    using_ground_truth = True

    # with open('ground_truth_results.csv', 'w') as csv_file:
    #     writer = csv.writer(csv_file)
    #     writer.writerow(["EXPERIMENT_ID", "PRIVACY", "TOTAL_PAIRS",
    #                      "A_RANDOM", "B_RANDOM", "C_RANDOM", "UNF_RANDOM",
    #                      "A_LEAST_COST", "B_LEAST_COST", "C_LEAST_COST", "UNF_LEAST_COST",
    #                      "A_LEAST_ATTACKERS", "B_LEAST_ATTACKERS", "C_LEAST_ATTACKERS", "UNF_LEAST_ATTACKERS",
    #                      "A_MOST_ATTACKS", "B_MOST_ATTACKS", "C_MOST_ATTACKS", "UNF_MOST_ATTACKS",
    #                      "A_GROUND_TRUTH", "B_GROUND_TRUTH", "C_GROUND_TRUTH"])
    #     csv_file.close()

    init = lambda pb=max_privacy_budget: [[] for x in range(pb)]
    agg_results_tau_random = init()
    agg_results_tau_least_cost = init()
    agg_results_tau_least_attackers = init()
    agg_results_tau_most_attacks = init()

    agg_results_local_unf_random = init()
    agg_results_local_unf_least_cost = init()
    agg_results_local_unf_least_attackers = init()
    agg_results_local_unf_most_attacks = init()

    ground_truth_distance = 0

    overall_data = {}

    experiment_id = -1
    while i < num_experiments:
        i += 1

        with open('experiment_id', "r") as id_file:
            experiment_id = int(id_file.read())
            id_file.close()
        base_queue = AgentQueue(ArgStrategy.ALL_ARGS, culture=BoatCulture(), size=queue_size,
                                privacy_budget=max_privacy_budget)
        print("\nExperiment {}".format(experiment_id))
        t_before_experiment = time.time()
        random.seed(experiment_id)
        experiment_data = overall_data[experiment_id] = {}
        experiment_data["experiment_id"] = experiment_id
        experiment_data["num_agents"] = queue_size
        experiment_data["agents"] = base_queue.agents_to_dict()
        experiment_data["results"] = {}
        experiment_data["results"]["per_strategy"] = {}

        a_gt = b_gt = c_gt = 0
        if test_type == 'ordering':
            baseline_random = copy.deepcopy(base_queue)
            baseline_random.set_strategy(ArgStrategy.RANDOM_CHOICE_NO_PRIVACY)
            baseline_random.interact_all()

            baseline_least_cost = copy.deepcopy(base_queue)
            baseline_least_cost.set_strategy(ArgStrategy.LEAST_COST_NO_PRIVACY)
            baseline_least_cost.interact_all()

            baseline_least_attackers = copy.deepcopy(base_queue)
            baseline_least_attackers.set_strategy(ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY)
            baseline_least_attackers.interact_all()

            baseline_most_attackers = copy.deepcopy(base_queue)
            baseline_most_attackers.set_strategy(ArgStrategy.MOST_ATTACKS_NO_PRIVACY)
            baseline_most_attackers.interact_all()
        elif test_type == 'matrix':
            if using_ground_truth:
                baseline_general = copy.deepcopy(base_queue)
                tbefore = time.time()
                baseline_general = baseline_general.compute_ground_truth_matrix_parallel()
                delta = time.time() - tbefore
                print("Time computing ground truth matrix: {:.0f}s".format(delta))
                baseline_random = baseline_general
                baseline_least_cost = baseline_general
                baseline_least_attackers = baseline_general
                baseline_most_attackers = baseline_general
                a_gt, b_gt, c_gt, total_pairs = dag_distance(base_queue, baseline_general, baseline_general, 0, 0)
                print("\nGround truth distance: {}".format(ground_truth_distance))
            else:
                baseline_random = copy.deepcopy(base_queue)
                baseline_random.set_strategy(ArgStrategy.RANDOM_CHOICE_NO_PRIVACY)
                baseline_random = baseline_random.interact_all_matrix()

                baseline_least_cost = copy.deepcopy(base_queue)
                baseline_least_cost.set_strategy(ArgStrategy.LEAST_COST_NO_PRIVACY)
                baseline_least_cost = baseline_least_cost.interact_all_matrix()

                baseline_least_attackers = copy.deepcopy(base_queue)
                baseline_least_attackers.set_strategy(ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY)
                baseline_least_attackers = baseline_least_attackers.interact_all_matrix()

                baseline_most_attackers = copy.deepcopy(base_queue)
                baseline_most_attackers.set_strategy(ArgStrategy.MOST_ATTACKS_NO_PRIVACY)
                baseline_most_attackers = baseline_most_attackers.interact_all_matrix()
        random_results = experiment_data["results"]["per_strategy"][str(ArgStrategy.RANDOM_CHOICE_PRIVATE)] = {}
        least_cost_results = experiment_data["results"]["per_strategy"][str(ArgStrategy.LEAST_COST_PRIVATE)] = {}
        most_att_results = experiment_data["results"]["per_strategy"][str(ArgStrategy.MOST_ATTACKS_PRIVATE)] = {}
        least_att_results = experiment_data["results"]["per_strategy"][str(ArgStrategy.LEAST_ATTACKERS_PRIVATE)] = {}
        csv_rows = []
        for g in range(0, max_privacy_budget, 1):
            print("{}".format(g), end=" ")

            random.seed(experiment_id)
            a_random, b_random, c_random, tp, uf_random, queue_data = run_test(base_queue, baseline_random, g,
                                                                               ArgStrategy.RANDOM_CHOICE_PRIVATE,
                                                                               test_type)
            random_results[g] = queue_data

            a_least_cost, b_least_cost, c_least_cost, tp, uf_least_cost, queue_data = run_test(base_queue,
                                                                                               baseline_least_cost, g,
                                                                                               ArgStrategy.LEAST_COST_PRIVATE,
                                                                                               test_type)
            least_cost_results[g] = queue_data

            a_most_att, b_most_att, c_most_att, tp, uf_most_att, queue_data = run_test(base_queue,
                                                                                       baseline_most_attackers, g,
                                                                                       ArgStrategy.MOST_ATTACKS_PRIVATE,
                                                                                       test_type)
            most_att_results[g] = queue_data

            a_least_att, b_least_att, c_least_att, tp, uf_least_att, queue_data = run_test(base_queue,
                                                                                           baseline_least_attackers, g,
                                                                                           ArgStrategy.LEAST_ATTACKERS_PRIVATE,
                                                                                           test_type)
            least_att_results[g] = queue_data

            # agg_results_tau_random[g].append(tau_random_with_privacy - ground_truth_distance)
            # agg_results_tau_least_cost[g].append(tau_least_cost_private - ground_truth_distance)
            # agg_results_tau_least_attackers[g].append(tau_least_attackers_private - ground_truth_distance)
            # agg_results_tau_most_attacks[g].append(tau_most_attacks_private - ground_truth_distance)
            #
            # agg_results_local_unf_random[g].append(uf_random_with_privacy)
            # agg_results_local_unf_least_cost[g].append(uf_least_cost_private)
            # agg_results_local_unf_least_attackers[g].append(uf_least_attackers_private)
            # agg_results_local_unf_most_attacks[g].append(uf_most_attacks_private)

            # ["EXPERIMENT_ID", "PRIVACY", "TOTAL_PAIRS"
            #                              "A_RANDOM", "B_RANDOM", "C_RANDOM", "UNF_RANDOM",
            #  "A_LEAST_COST", "B_LEAST_COST", "C_LEAST_COST", "UNF_LEAST_COST"
            #                                                  "A_LEAST_ATTACKERS", "B_LEAST_ATTACKERS",
            #  "C_LEAST_ATTACKERS", "UNF_LEAST_ATTACKERS",
            #  "A_MOST_ATTACKS", "B_MOST_ATTACKS", "C_MOST_ATTACKS", "UNF_MOST_ATTACKS",
            #  "A_GROUND_TRUTH", "B_GROUND_TRUTH", "C_GROUND_TRUTH"]

            csv_rows.append([experiment_id, g, tp,
                     a_random, b_random, c_random, uf_random,
                     a_least_cost, b_least_cost, c_least_cost, uf_least_cost,
                     a_least_att, b_least_att, c_least_att, uf_least_att,
                     a_most_att, b_most_att, c_most_att, uf_most_att,
                     a_gt, b_gt, c_gt])


        delta = time.time() - t_before_experiment
        print("Time running experiment {}: {:.0f}s".format(i, delta))
        print("Saving to CSV...")
        with open('ground_truth_results.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            for row in csv_rows:
                writer.writerow(row)
            csv_file.close()
        print("Saving to JSON...")
        with open('experiment_data.json', 'w') as json_file:
            json.dump(experiment_data, json_file, indent=2)
        with open('experiment_id', "w") as id_file:
            id_file.write(str(experiment_id + 1))
            id_file.close()

    t1 = time.time() - t0
    print("Time elapsed: {}".format(t1))

    figure, axs = plt.subplots(2, 4)
    # # plt.xticks(rotation=90)
    # for row in axs:
    #     for ax in row:
    #         ax.xticks(rotation=90)
    ax_random_tau = axs[0, 0]
    ax_random_unf = axs[1, 0]
    ax_least_cost_tau = axs[0, 1]
    ax_least_cost_unf = axs[1, 1]
    ax_least_attackers_tau = axs[0, 2]
    ax_least_attackers_unf = axs[1, 2]
    ax_most_attacks_tau = axs[0, 3]
    ax_most_attacks_unf = axs[1, 3]

    ######################
    # RANDOM #############
    ######################

    # figure_random_tau, ax_random_tau = plt.subplots()
    ax_random_tau.set_title("Random private x non-private\n({} iterations. {} agents in queue. )".format(
        num_experiments, queue_size
    ))
    ax_random_tau.boxplot(agg_results_tau_random, showfliers=False, showmeans=True)
    # ax.legend(labels)
    ax_random_tau.set_ylabel("Kendall tau value")
    if test_type == 'ordering':
        ax_random_tau.axhline(y=1.0, color='r')
        ax_random_tau.axhline(y=0.0, color='g')
        ax_random_tau.set_ylim(top=1.05)

    # figure_random_unf, ax_random_unf = plt.subplots()
    # ax2 = ax.twinx()
    ax_random_unf.set_ylabel("Rate of unfair interactions")
    ax_random_unf.set_title("Interactions ended by shortness of budget.\n(random)")
    ax_random_unf.boxplot(agg_results_local_unf_random, showfliers=False, showmeans=True, patch_artist=True)
    ax_random_unf.set_ylim(top=0.55)

    ######################
    # LEAST ATTACKERS ####
    ######################

    # figure_least_attackers_tau, ax_least_attackers_tau = plt.subplots()
    ax_least_attackers_tau.set_title(
        "Least attackers private x non-private\n({} iterations. {} agents in queue. )".format(
            num_experiments, queue_size
        ))
    ax_least_attackers_tau.boxplot(agg_results_tau_least_attackers, showfliers=False, showmeans=True)
    # ax.legend(labels)
    ax_least_attackers_tau.set_ylabel("Kendall tau value")
    if test_type == 'ordering':
        ax_least_attackers_tau.axhline(y=1.0, color='r')
        ax_least_attackers_tau.axhline(y=0.0, color='g')
        ax_least_attackers_tau.set_ylim(top=1.05)

    # figure_least_attackers_unf, ax_least_attackers_unf = plt.subplots()
    # ax2 = ax.twinx()
    ax_least_attackers_unf.set_ylabel("Rate of unfair interactions")
    ax_least_attackers_unf.set_title("Interactions ended by shortness of budget.\n(least attackers)")
    ax_least_attackers_unf.boxplot(agg_results_local_unf_least_attackers, showfliers=False, showmeans=True,
                                   patch_artist=True)
    ax_least_attackers_unf.set_ylim(top=0.55)

    ######################
    # LEAST COST #########
    ######################

    # figure_least_cost_tau, ax_least_cost_tau = plt.subplots()
    ax_least_cost_tau.set_title(
        "Least cost private x non-private\n({} iterations. {} agents in queue. )".format(
            num_experiments, queue_size
        ))
    ax_least_cost_tau.boxplot(agg_results_tau_least_cost, showfliers=False, showmeans=True)
    # ax.legend(labels)
    ax_least_cost_tau.set_ylabel("Kendall tau value")
    if test_type == 'ordering':
        ax_least_cost_tau.axhline(y=1.0, color='r')
        ax_least_cost_tau.axhline(y=0.0, color='g')
        ax_least_cost_tau.set_ylim(top=1.05)

    # figure_least_cost_unf, ax_least_cost_unf = plt.subplots()
    # ax2 = ax.twinx()
    ax_least_cost_unf.set_ylabel("Rate of unfair interactions")
    ax_least_cost_unf.set_title("Interactions ended by shortness of budget.\n(least cost)")
    ax_least_cost_unf.boxplot(agg_results_local_unf_least_cost, showfliers=False, showmeans=True,
                              patch_artist=True)
    ax_least_cost_unf.set_ylim(top=0.55)

    ######################
    # MOST ATTACKS #######
    ######################

    # figure_most_attacks_tau, ax_most_attacks_tau = plt.subplots()
    ax_most_attacks_tau.set_title("Most attacks private x non-private\n({} iterations. {} agents in queue. )".format(
        num_experiments, queue_size
    ))
    ax_most_attacks_tau.boxplot(agg_results_tau_most_attacks, showfliers=False, showmeans=True)
    # ax.legend(labels)
    ax_most_attacks_tau.set_ylabel("Kendall tau value")
    if test_type == 'ordering':
        ax_most_attacks_tau.axhline(y=1.0, color='r')
        ax_most_attacks_tau.axhline(y=0.0, color='g')
        ax_most_attacks_tau.set_ylim(top=1.05)

    # figure_most_attacks_unf, ax_most_attacks_unf = plt.subplots()
    # ax2 = ax.twinx()
    ax_most_attacks_unf.set_ylabel("Rate of unfair interactions")
    ax_most_attacks_unf.set_title("Interactions ended by shortness of budget.\n(most attackers)")
    ax_most_attacks_unf.boxplot(agg_results_local_unf_most_attacks, showfliers=False, showmeans=True, patch_artist=True)
    ax_most_attacks_unf.set_ylim(top=0.55)

    plt.show()


def benchmark(num_iterations, queue_size, privacy_budget, test_type='ordering'):
    t0 = time.time()
    result_random_with_privacy = []
    result_random_without_privacy = []
    result_least_attackers_private = []
    result_least_attackers_no_privacy = []
    result_most_attacks_private = []
    result_most_attacks_no_privacy = []
    result_all_args = []
    result_greedy = []

    unfairness_random_with_privacy = []
    unfairness_random_without_privacy = []
    unfairness_least_attackers_private = []
    unfairness_least_attackers_no_privacy = []
    unfairness_most_attacks_private = []
    unfairness_most_attacks_no_privacy = []
    unfairness_all_args = []
    unfairness_greedy = []

    i = 0

    while i < num_iterations:
        print("Iteration {} of {}".format(i, num_iterations))
        base_queue = AgentQueue(ArgStrategy.ALL_ARGS, size=queue_size, privacy_budget=privacy_budget)

        logging.debug("\n*\n*\n GROUND TRUTH \n*\n*\n")
        status_quo = {}
        baseline = copy.deepcopy(base_queue)
        if test_type == 'ordering':
            baseline, predicted_swaps, actual_swaps, status_quo = baseline.compute_ground_truth()
        elif test_type == 'matrix':
            baseline = baseline.compute_ground_truth_matrix()
        total_order = 0
        partial_order = 0
        for pair, outcome in status_quo.items():
            defender, challenger = pair
            if status_quo[(defender, challenger)] != status_quo[(challenger, defender)]:
                total_order += 1
            else:
                partial_order += 1
                # print("Partial order: {} {}".format(defender, challenger))
        total_pairs = len(status_quo)
        print("Total pairs tested: {}".format(total_pairs))
        print("Guaranteed order: {}".format(total_order))
        print("Resource dependent: {}".format(partial_order))
        # if partial_order > 2:
        #     print("OH NO!")
        #     exit(0)
        #     continue
        i += 1

        # if total_order <= (total_pairs / 2):
        #     i -= 1
        #     print("\nRETRY\n")
        #     baseline = copy.deepcopy(base_queue)
        #     print("BASE CULTURE:\n{}".format(baseline.culture.argumentation_framework.to_aspartix_text()))
        #     for agent in baseline.queue:
        #         print("Agent {}'s properties: {}".format(agent.id, agent.properties))
        #
        #     baseline, predicted_swaps, actual_swaps, status_quo = baseline.compute_ground_truth(debug=False)
        #     print("SWAPS: {}".format(status_quo))
        #     logging.debug("\n*\n*\n RANDOM WITH PRIVACY \n*\n*\n")
        #     # Test random with privacy
        #     tau_random_with_privacy, uf_random_with_privacy = run_test(base_queue, baseline,
        #                                                                ArgStrategy.RANDOM_CHOICE_PRIVATE,
        #                                                                RANDOM_SAMPLES)
        #     logging.debug("Kendall Tau value: {}".format(tau_random_with_privacy))
        #
        #     logging.debug("\n*\n*\n STRATEGIC WITH PRIVACY \n*\n*\n")
        #     # Test strategic direct with privacy
        #     tau_least_attackers_private, uf_least_attackers_private = run_test(base_queue, baseline,
        #                                                                        ArgStrategy.LEAST_ATTACKERS_PRIVATE)
        #     logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))
        #     exit(0)
        # else:
        #     continue

        logging.debug("\n*\n*\n RANDOM WITH PRIVACY \n*\n*\n")
        # Test random with privacy
        tau_random_with_privacy, uf_random_with_privacy = run_test(base_queue, baseline, privacy_budget,
                                                                   ArgStrategy.RANDOM_CHOICE_PRIVATE, test_type)
        logging.debug("Kendall Tau value: {}".format(tau_random_with_privacy))

        logging.debug("\n*\n*\n GREEDY WITH PRIVACY \n*\n*\n")
        # Test greedy with privacy
        tau_greedy_with_privacy, uf_greedy_with_privacy = run_test(base_queue, baseline, privacy_budget,
                                                                   ArgStrategy.LEAST_COST_PRIVATE, test_type)
        logging.debug("Kendall Tau value: {}".format(tau_greedy_with_privacy))

        logging.debug("\n*\n*\n LEAST ATTACKERS WITH PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_least_attackers_private, uf_least_attackers_private = run_test(base_queue, baseline, privacy_budget,
                                                                           ArgStrategy.LEAST_ATTACKERS_PRIVATE,
                                                                           test_type)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n LEAST ATTACKERS NO PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_least_attackers_no_privacy, uf_least_attackers_no_privacy = run_test(base_queue, baseline, privacy_budget,
                                                                                 ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY,
                                                                                 test_type)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n MOST ATTACKS WITH PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_most_attacks_private, uf_most_attacks_private = run_test(base_queue, baseline, privacy_budget,
                                                                     ArgStrategy.MOST_ATTACKS_PRIVATE, test_type)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n MOST ATTACKS NO PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_most_attacks_no_privacy, uf_most_attacks_no_privacy = run_test(base_queue, baseline, privacy_budget,
                                                                           ArgStrategy.MOST_ATTACKS_NO_PRIVACY,
                                                                           test_type)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n ALL ARGS \n*\n*\n")
        # Test strategic relative with privacy
        tau_all_args, uf_all_args = run_test(base_queue, baseline, privacy_budget, ArgStrategy.ALL_ARGS, test_type)
        logging.debug("Kendall Tau value: {}".format(result_all_args))

        logging.debug("\n*\n*\n RANDOM NO PRIVACY \n*\n*\n")
        # Test random without privacy
        tau_random_without_privacy, uf_random_without_privacy = run_test(base_queue, baseline, privacy_budget,
                                                                         ArgStrategy.RANDOM_CHOICE_NO_PRIVACY,
                                                                         test_type)
        logging.debug("Kendall Tau value: {}".format(tau_random_without_privacy))

        # Collate results.
        result_random_with_privacy.append(tau_random_with_privacy)
        result_greedy.append(tau_greedy_with_privacy)
        result_random_without_privacy.append(tau_random_without_privacy)
        result_least_attackers_private.append(tau_least_attackers_private)
        result_least_attackers_no_privacy.append(tau_least_attackers_no_privacy)
        result_most_attacks_private.append(tau_most_attacks_private)
        result_most_attacks_no_privacy.append(tau_most_attacks_no_privacy)
        result_all_args.append(tau_all_args)

        unfairness_random_with_privacy.append(uf_random_with_privacy)
        unfairness_greedy.append(uf_greedy_with_privacy)
        unfairness_random_without_privacy.append(uf_random_without_privacy)
        unfairness_least_attackers_private.append(uf_least_attackers_private)
        unfairness_least_attackers_no_privacy.append(uf_least_attackers_no_privacy)
        unfairness_most_attacks_private.append(uf_most_attacks_private)
        unfairness_most_attacks_no_privacy.append(uf_most_attacks_no_privacy)
        unfairness_all_args.append(uf_all_args)

    results_tau = [result_random_with_privacy,
                   result_random_without_privacy,
                   result_greedy,
                   result_least_attackers_private,
                   result_least_attackers_no_privacy,
                   result_most_attacks_private,
                   result_most_attacks_no_privacy,
                   result_all_args]

    results_unfairness = [unfairness_random_with_privacy,
                          unfairness_random_without_privacy,
                          unfairness_greedy,
                          unfairness_least_attackers_private,
                          unfairness_least_attackers_no_privacy,
                          unfairness_most_attacks_private,
                          unfairness_most_attacks_no_privacy,
                          unfairness_all_args]

    labels = ["1. Random and Private", "2. Random no Privacy", "3. Least Cost and Private",
              "4. Least Attackers and Private", "5. Least Attackers no Privacy", "6. Most Attacks and Private",
              "7. Most Attacks no Privacy", "8. Multiple args "]
    t1 = time.time() - t0
    print("Time elapsed: {}".format(t1))

    figure, ax = plt.subplots()
    ax.set_title("Similarity to ground truth\n({} iterations. {} agents in queue. Privacy budget {}.)".format(
        num_iterations, queue_size, privacy_budget
    ))
    ax.boxplot(results_tau, showfliers=False, showmeans=True)
    ax.legend(labels)
    ax.set_ylabel("DAG distance\n(lower is better)")
    # plt.axhline(y=1.0, color='r')
    # plt.axhline(y=0.0, color='g')
    # plt.ylim(top=1.05)

    figure2, ax2 = plt.subplots()
    # ax2 = ax.twinx()
    ax2.set_ylabel("Rate of unfair interactions")
    ax2.set_title("Interactions ended by shortness of budget.\n(Privacy budget {}.)".format(privacy_budget))
    ax2.legend(labels)
    ax2.boxplot(results_unfairness, showfliers=False, showmeans=True, patch_artist=True)

    plt.show()


# benchmark(num_iterations = 30, queue_size = 20, privacy_budget = 10, test_type='matrix')
benchmark_same_strategy(num_experiments=1, queue_size=16, max_privacy_budget=80, test_type='matrix')
