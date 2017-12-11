from multiprocessing.pool import ThreadPool

def main(start_queue, function_call,
         thread_count=1, cleanup_max=5,
         index="Status",
         error_value="Failed"):
    """
    @Block
    :desc: Take a list of items, dicts or lists, and process them with multiple threads.
           If a list, you can set the status index which will be checked after each round.
           If a dict, you can set the status key which will be checked after each round.

    :param start_queue: A list of elements to process
    :type start_queue: list
    :example start_queue: [{"number": 1}, {"number": 2}]

    :param function_call: A function that takes in an element of start_queue and
                          returns an updated element with its status.
    :type function_call: function

    :param thread_count: How many threads to run in parallel
    :type thread_count: int
    :example thread_count: 2

    :param cleanup_max: How many times to process failed messages in the queue
    :type cleanup_max: int
    :example cleanup_max: 3

    :param list_index: This specifies the index of the status if the element is a list and 
                       the key of the status if the element is a dict.
    :type list_index: int or string
    :example list_index: 0 or "Status"

    :param error_value: This specifies the value of the status if failed, which will be set in the function.
    :type error_value: string
    :example error_value: "Failed"

    :returns: A list of the processed elements from the start_queue
    :rtype: list
    :example: [{"number":2"}, {"number": 4}]
    """

    count, finished_queue = 0, []

    while start_queue and count < cleanup_max:
        print "Starting with {} objects in queue and {} threads. On count {} of {}".format(len(start_queue), thread_count,
                                                                                           count, cleanup_max)

        current_queue = start_queue
        start_queue = []

        pool = ThreadPool(thread_count)
        results = pool.map(function_call,current_queue)
        pool.close()
        pool.join()

        for i in range(len(results)):
            if results[i][index] == error_value:
                results[i][index] = "In Queue"
                start_queue.append(results[i])
            else:
                finished_queue.append(results[i])

        print "Finished {} elements. Retrying {} elements. On count {} of {}".format(len(finished_queue),
                                                                                     len(start_queue),
                                                                                     count,
                                                                                     cleanup_max)
        count += 1

    return finished_queue
