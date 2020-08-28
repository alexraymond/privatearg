from agent_queue import *
import matplotlib.pyplot as plt
import time
import numpy as np

RANDOM_SAMPLES = 10

def benchmark(num_iterations, queue_size, privacy_budget):
    t0 = time.time()
    result_random_with_privacy = []
    result_random_without_privacy = []
    result_count_occurrences_direct = []
    result_count_occurrences_relative = []
    result_greedy = []

    for i in range(num_iterations):
        print("Iteration {} of {}".format(i, num_iterations))
        base_queue = AgentQueue(ArgumentationStrategy.ALL_ARGS, size = queue_size, privacy_budget = privacy_budget)

        baseline = copy.deepcopy(base_queue)
        baseline.set_strategy(ArgumentationStrategy.ALL_ARGS)
        baseline.interact_all()

        # Test random with privacy
        random_with_privacy = 0.0
        for j in range(RANDOM_SAMPLES):
            q = copy.deepcopy(base_queue)
            q.set_strategy(ArgumentationStrategy.RANDOM_CHOICE_WITH_PRIVACY)
            q.interact_all()
            text, tau, p = q.relative_queue(ground_truth=baseline)
            random_with_privacy += tau / RANDOM_SAMPLES

        # Test greedy with privacy
        q = copy.deepcopy(base_queue)
        q.set_strategy(ArgumentationStrategy.GREEDY_MIN_PRIVACY)
        q.interact_all()
        text, tau, p = q.relative_queue(ground_truth=baseline)
        greedy_with_privacy = tau

        # Test strategic direct with privacy
        q1 = copy.deepcopy(base_queue)
        q1.set_strategy(ArgumentationStrategy.COUNT_OCCURRENCES_ADMISSIBLE_DIRECT)
        q1.interact_all()
        text, tau, p = q1.relative_queue(ground_truth=baseline)
        count_occurrences_direct = tau

        # Test strategic relative with privacy
        q1 = copy.deepcopy(base_queue)
        q1.set_strategy(ArgumentationStrategy.COUNT_OCCURRENCES_ADMISSIBLE_RELATIVE)
        q1.interact_all()
        text, tau, p = q1.relative_queue(ground_truth=baseline)
        count_occurrences_relative = tau

        # Test random without privacy
        random_without_privacy = 0.0
        for j in range(RANDOM_SAMPLES):
            q = copy.deepcopy(base_queue)
            q.set_strategy(ArgumentationStrategy.RANDOM_CHOICE_NO_PRIVACY)
            q.interact_all()
            text, tau, p = q.relative_queue(ground_truth=baseline)
            random_without_privacy += tau / RANDOM_SAMPLES

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


benchmark(num_iterations = 1, queue_size = 30, privacy_budget = 20)





