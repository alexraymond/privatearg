from agent_queue import *
import matplotlib.pyplot as plt
import time
import numpy as np

RANDOM_SAMPLES = 20

def run_test(base_queue, baseline, arg_strategy):
    q = copy.deepcopy(base_queue)
    q.set_strategy(arg_strategy)
    q.interact_all()
    text, tau, p = q.relative_queue(ground_truth=baseline)
    return tau

def run_averaged_test(base_queue, baseline, arg_strategy):
    averaged_tau = 0
    for i in range(RANDOM_SAMPLES):
        q = copy.deepcopy(base_queue)
        q.set_strategy(arg_strategy)
        q.interact_all()
        text, tau, p = q.relative_queue(ground_truth=baseline)
        averaged_tau += tau / RANDOM_SAMPLES
    return averaged_tau


def benchmark(num_iterations, queue_size, privacy_budget):
    t0 = time.time()
    result_random_with_privacy = []
    result_random_without_privacy = []
    result_count_occurrences_direct = []
    result_count_occurrences_relative = []
    result_greedy = []

    for i in range(num_iterations):
        print("Iteration {} of {}".format(i, num_iterations))
        base_queue = AgentQueue(ArgStrategy.ALL_ARGS, size = queue_size, privacy_budget = privacy_budget)

        baseline = copy.deepcopy(base_queue)
        baseline.set_strategy(ArgStrategy.ALL_ARGS)
        baseline.interact_all()

        # Test random with privacy
        random_with_privacy = run_averaged_test(base_queue, baseline, ArgStrategy.RANDOM_CHOICE_WITH_PRIVACY)

        # Test greedy with privacy
        greedy_with_privacy = run_test(base_queue, baseline, ArgStrategy.GREEDY_MIN_PRIVACY)

        # Test strategic direct with privacy
        count_occurrences_direct = run_test(base_queue, baseline,
                                            ArgStrategy.COUNT_OCCURRENCES_ADMISSIBLE_DIRECT)

        # Test strategic relative with privacy
        count_occurrences_relative = run_test(base_queue, baseline,
                                              ArgStrategy.COUNT_OCCURRENCES_ADMISSIBLE_RELATIVE)

        # Test random without privacy
        random_without_privacy = run_averaged_test(base_queue, baseline, ArgStrategy.RANDOM_CHOICE_NO_PRIVACY)

        # Collate results.
        result_random_with_privacy.append(random_with_privacy)
        result_greedy.append(greedy_with_privacy)
        result_random_without_privacy.append(random_without_privacy)
        result_count_occurrences_direct.append(count_occurrences_direct)
        result_count_occurrences_relative.append(count_occurrences_relative)

    results = [result_random_with_privacy, result_greedy, result_count_occurrences_direct,
               result_count_occurrences_relative,  result_random_without_privacy]
    labels = ["1. Random and Private", "2. Greedy and Private", "3. Strategic and Private (pure arg strength)",
              "4. Strategic and Private (relative)", "5. Random no Privacy"]
    t1 = time.time() - t0
    print("Time elapsed: {}".format(t1))
    figure, ax = plt.subplots()
    ax.set_title("Kendall Tau values (outliers removed)")
    ax.boxplot(results, showfliers=False)
    ax.legend(labels)
    plt.legend(labels)
    plt.axhline(y=1.0, color='r')
    plt.ylim(top=1.05)
    plt.show()


benchmark(num_iterations = 50, queue_size = 30, privacy_budget = 40)





