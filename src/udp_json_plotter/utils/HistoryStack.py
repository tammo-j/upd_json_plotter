class HistoryStack:
    """
    The HistoryStack acts like a normal Stack but providing a history benefit with forward and back functionality.

    To make use of the two basis stack functions put a new value onto the stack and pop the most recent value from the
    stack use the functions `append` and `back`. In addition of that a third function `forward` is offered, to
    be able to undo the last recent calls of back. Both `back` and `forward` will return the corresponding  most recent
    value from the HistoryStack.

    The usages intent is to store only the history but not the current state of a value itself. This implies that the
    current state of the observed value must always be passed as parameter `current_value` to all of the three main
    functions `append`, `back` and `forward`. This is necessary to utilize and provide the forward functionality.
    The function `back` and `forward` will not delete any value form the history. In contrast the `append` functions
    may discard values. As example this happens if at first `back` is called at a none empty HistoryStack and
    subsequently `append` is called. In this case the previous successor (and all followings) after the `back` call is
    deleted and substituted with the value of the `append` call. In general `append` will delete values from the
    HistoryStack every time if and only if `is_forward_feasible` will return 'True' beforehand `append` is called.

    To reset the whole HistoryStack to the initial state use the function `clear`.
    Moreover there are some retrieval functions starting with `is_` or `get_` to query the actual state.
    """

    def __init__(self):
        self._stack = []
        self._index = -1
        self._validate_index()

    def append(self, current_value):
        """ append will discard possible successors if any so that forward will return 'None' afterwards """
        self._index += 1
        del self._stack[self._index:]  # discard possible successors
        self._stack.append(current_value)
        self._validate_index()

    def back(self, current_value):
        """
        The parameter current_value is mandatory to provide forward functionality afterwards.
        The usage looks like `current_value = history_stack.back(current_value)`.
        """
        if not self.is_back_feasible():
            return None  # no predecessor
        most_recent_value = self._stack[self._index]
        self._stack[self._index] = current_value
        self._index -= 1
        self._validate_index()
        return most_recent_value

    def forward(self, current_value):
        """
        The parameter current_value is mandatory to provide back functionality afterwards.
        The usage looks like `current_value = history_stack.forward(current_value)`.
        """
        if not self.is_forward_feasible():
            return None  # no successor
        self._index += 1
        most_recent_value = self._stack[self._index]
        self._stack[self._index] = current_value
        self._validate_index()
        return most_recent_value

    def clear(self):
        self._stack.clear()
        self._index = -1
        self._validate_index()

    def is_empty(self):
        return len(self._stack) == 0

    def is_back_feasible(self):
        return self._index >= 0

    def is_forward_feasible(self):
        return self._index < len(self._stack)-1

    def get_number_of_feasible_back_steps(self):
        return self._index + 1

    def get_number_of_feasible_forward_steps(self):
        return len(self._stack)-1 - self._index

    def _validate_index(self):
        assert self._index >= -1, f'self._index={self._index} may not below -1!'
        assert self._index < len(self._stack), f'self._index={self._index} may not above ' \
            f'len(self._stack)={len(self._stack)}!'
