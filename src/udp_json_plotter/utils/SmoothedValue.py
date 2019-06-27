class SmoothedValue:
    def __init__(self, initial_value=None, smoothing_factor=1):
        if initial_value is not None:
            self._is_initialized = True
        else:
            self._is_initialized = False
        self._value = initial_value
        self._strong_smoothed_value = initial_value
        assert 0 <= smoothing_factor <= 1
        self._smoothing_factor = smoothing_factor
        self._max_value_deviation = 0.1

    def __lazy_init__(self, initial_value):
        self._value = initial_value
        self._strong_smoothed_value = initial_value
        self._is_initialized = True

    @property
    def value(self):
        return self._value

    @property
    def smoothing_factor(self):
        return self._smoothing_factor

    @smoothing_factor.setter
    def smoothing_factor(self, smoothing_factor):
        assert 0 <= smoothing_factor <= 1
        print(f'Set rotation smoothing_factor to {smoothing_factor}.')
        self._smoothing_factor = smoothing_factor

    def update(self, new_value):
        if self._smoothing_factor == 0:
            self._value = new_value
            self._is_initialized = False
            return
        if self._is_initialized is False:
            self.__lazy_init__(new_value)
            return
        self._strong_smoothed_value = 0.1 * new_value + 0.9 * self._strong_smoothed_value
        deviation = abs(self._strong_smoothed_value - new_value)
        deviation_ratio = max(0, min(1, deviation / self._max_value_deviation))
        smoothing_factor = self._smoothing_factor * (1 - deviation_ratio)
        self._value = (1 - smoothing_factor) * new_value + smoothing_factor * self._value
