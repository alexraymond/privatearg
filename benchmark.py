from agent_queue import *
import matplotlib.pyplot as plt
import time
import numpy as np

RANDOM_SAMPLES = 10

def run_test(base_queue, baseline, arg_strategy, num_samples=1):
    averaged_tau = 0
    for i in range(num_samples):
        q = copy.deepcopy(base_queue)
        q.set_strategy(arg_strategy)
        q.interact_all()
        text, tau, p = q.relative_queue(ground_truth=baseline)
        # if num_samples == 1:
        #     print("Relative queue {}".format(text))
        averaged_tau += tau / num_samples
    return averaged_tau


def benchmark(num_iterations, queue_size, privacy_budget):
    t0 = time.time()
    result_random_with_privacy = []
    result_random_without_privacy = []
    result_least_attackers_private = []
    result_least_attackers_no_privacy = []
    result_greedy = []

    for i in range(num_iterations):
        print("Iteration {} of {}".format(i, num_iterations))
        base_queue = AgentQueue(ArgStrategy.ALL_ARGS, size = queue_size, privacy_budget = privacy_budget)

        logging.debug("\n*\n*\n GROUND TRUTH \n*\n*\n")
        baseline = copy.deepcopy(base_queue)
        baseline.set_strategy(ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY)
        baseline.interact_all()
        # print(baseline.bw_framework.to_aspartix_text())

        logging.debug("\n*\n*\n RANDOM WITH PRIVACY \n*\n*\n")
        # Test random with privacy
        random_with_privacy = run_test(base_queue, baseline, ArgStrategy.RANDOM_CHOICE_PRIVATE, RANDOM_SAMPLES)
        logging.debug("Kendall Tau value: {}".format(random_with_privacy))
        logging.debug("\n*\n*\n GREEDY WITH PRIVACY \n*\n*\n")
        # Test greedy with privacy
        greedy_with_privacy = run_test(base_queue, baseline, ArgStrategy.GREEDY_MIN_PRIVACY)
        logging.debug("Kendall Tau value: {}".format(greedy_with_privacy))

        logging.debug("\n*\n*\n STRATEGIC WITH PRIVACY \n*\n*\n")
        # Test strategic direct with privacy
        least_attackers_private = run_test(base_queue, baseline,
                                            ArgStrategy.LEAST_ATTACKERS_PRIVATE)
        logging.debug("Kendall Tau value: {}".format(least_attackers_private))

        logging.debug("\n*\n*\n STRATEGIC NO PRIVACY \n*\n*\n")
        # Test strategic relative with privacy
        least_attackers_no_privacy = run_test(base_queue, baseline,
                                                     ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY)
        logging.debug("Kendall Tau value: {}".format(result_least_attackers_no_privacy))

        logging.debug("\n*\n*\n RANDOM NO PRIVACY \n*\n*\n")
        # Test random without privacy
        random_without_privacy = run_test(base_queue, baseline, ArgStrategy.RANDOM_CHOICE_NO_PRIVACY, RANDOM_SAMPLES)
        logging.debug("Kendall Tau value: {}".format(random_without_privacy))

        # Collate results.
        result_random_with_privacy.append(random_with_privacy)
        result_greedy.append(greedy_with_privacy)
        result_random_without_privacy.append(random_without_privacy)
        result_least_attackers_private.append(least_attackers_private)
        result_least_attackers_no_privacy.append(least_attackers_no_privacy)

    results = [result_random_with_privacy, result_greedy, result_least_attackers_private,
               result_least_attackers_no_privacy,  result_random_without_privacy]
    labels = ["1. Random and Private", "2. Cheapest and Private", "3. Least Attackers and Private",
              "4. Least Attackers no Privacy", "5. Random no Privacy"]
    t1 = time.time() - t0
    print("Time elapsed: {}".format(t1))
    figure, ax = plt.subplots()
    ax.set_title("Kendall Tau values (outliers removed)")
    ax.boxplot(results, showfliers=False, showmeans=True)
    ax.legend(labels)
    plt.legend(labels)
    plt.axhline(y=1.0, color='r')
    plt.ylim(top=1.05)
    plt.show()


benchmark(num_iterations = 100, queue_size = 30, privacy_budget = 20)





