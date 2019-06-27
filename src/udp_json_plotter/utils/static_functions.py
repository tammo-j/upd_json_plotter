def first_index(iterable, condition):
    for index, item in enumerate(iterable):
        if condition(item):
            return index
    return None


def last_index(iterable, condition):
    index_reversed = first_index(reversed(iterable), condition)
    if index_reversed is None:
        return None
    return len(iterable) - index_reversed - 1
