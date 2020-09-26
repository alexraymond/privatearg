from agent_queue import *
import matplotlib.pyplot as plt
import time
import numpy as np

RANDOM_SAMPLES = 1

def run_test(base_queue, baseline, arg_strategy, num_samples=1):
    averaged_tau = 0
    averaged_unfairness = 0
    for i in range(num_samples):
        q = copy.deepcopy(base_queue)
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
        # if num_samples == 1:
        #     print("Relative queue {}".format(text))
        averaged_tau += tau / num_samples
        averaged_unfairness += q.rate_local_unfairness / num_samples
    return averaged_tau, averaged_unfairness


def benchmark(num_iterations, queue_size, privacy_budget):
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
        base_queue = AgentQueue(ArgStrategy.ALL_ARGS, size = queue_size, privacy_budget = privacy_budget)

        logging.debug("\n*\n*\n GROUND TRUTH \n*\n*\n")
        status_quo = {}
        baseline = copy.deepcopy(base_queue)
        baseline, predicted_swaps, actual_swaps, status_quo = baseline.compute_ground_truth()
        total_order = 0
        partial_order = 0
        for pair, outcome in status_quo.items():
            defender, challenger = pair
            if status_quo[(defender,challenger)] != status_quo[(challenger,defender)]:
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
        tau_random_with_privacy, uf_random_with_privacy = run_test(base_queue, baseline, ArgStrategy.RANDOM_CHOICE_PRIVATE, RANDOM_SAMPLES)
        logging.debug("Kendall Tau value: {}".format(tau_random_with_privacy))

        logging.debug("\n*\n*\n GREEDY WITH PRIVACY \n*\n*\n")
        # Test greedy with privacy
        tau_greedy_with_privacy, uf_greedy_with_privacy = run_test(base_queue, baseline, ArgStrategy.GREEDY_MIN_PRIVACY)
        logging.debug("Kendall Tau value: {}".format(tau_greedy_with_privacy))

        logging.debug("\n*\n*\n LEAST ATTACKERS WITH PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_least_attackers_private, uf_least_attackers_private = run_test(base_queue, baseline,
                                                                           ArgStrategy.LEAST_ATTACKERS_PRIVATE)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n LEAST ATTACKERS NO PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_least_attackers_no_privacy, uf_least_attackers_no_privacy = run_test(base_queue, baseline,
                                                                                 ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n MOST ATTACKS WITH PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_most_attacks_private, uf_most_attacks_private = run_test(base_queue, baseline,
                                                                           ArgStrategy.MOST_ATTACKS_PRIVATE)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n MOST ATTACKS NO PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        tau_most_attacks_no_privacy, uf_most_attacks_no_privacy = run_test(base_queue, baseline,
                                                                                 ArgStrategy.MOST_ATTACKS_NO_PRIVACY)
        logging.debug("Kendall Tau value: {}".format(tau_least_attackers_private))

        logging.debug("\n*\n*\n ALL ARGS \n*\n*\n")
        # Test strategic relative with privacy
        tau_all_args, uf_all_args = run_test(base_queue, baseline, ArgStrategy.ALL_ARGS)
        logging.debug("Kendall Tau value: {}".format(result_all_args))

        logging.debug("\n*\n*\n RANDOM NO PRIVACY \n*\n*\n")
        # Test random without privacy
        tau_random_without_privacy, uf_random_without_privacy = run_test(base_queue, baseline, ArgStrategy.RANDOM_CHOICE_NO_PRIVACY, RANDOM_SAMPLES)
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
              "4. Least Attackers and Private", "5. Least Attackers no Privacy", "6. Most Attacks and Private", "7. Most Attacks no Privacy",  "8. Multiple args "]
    t1 = time.time() - t0
    print("Time elapsed: {}".format(t1))

    figure, ax = plt.subplots()
    ax.set_title("Similarity to ground truth\n({} iterations. {} agents in queue. Privacy budget {}.)".format(
        num_iterations, queue_size, privacy_budget
    ))
    ax.boxplot(results_tau, showfliers=True, showmeans=True)
    ax.legend(labels)
    ax.set_ylabel("Kendall tau value")
    plt.axhline(y=1.0, color='r')
    plt.axhline(y=0.0, color='g')
    plt.ylim(top=1.05)

    figure2, ax2 = plt.subplots()
    # ax2 = ax.twinx()
    ax2.set_ylabel("Rate of unfair interactions")
    ax2.set_title("Interactions ended by shortness of budget.\n(Privacy budget {}.)".format(privacy_budget))
    ax2.legend(labels)
    ax2.boxplot(results_unfairness, showfliers=True, showmeans=True, patch_artist=True)

    plt.show()


benchmark(num_iterations = 10, queue_size = 20, privacy_budget = 20)





