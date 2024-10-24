import pandas as pd
from .ws_base import Work_location


class ODMatrixSelect(Work_location):
    def __init__(self, rng):
        Work_location.__init__(self, rng)

        self._weights = {}

    def init(self, filename):
        transition = pd.read_csv(filename, delimiter=',', index_col=0)
        for idx, row in transition.iterrows():
            row = row.dropna()
            row_sum = row.sum()
            row = row.divide(row_sum)
            self._weights[idx] = row

    def obtain(self, idx):
        try:
            row = self._weights[idx]
            weights = row.values
            val = self._rng.choice(len(weights), 1, p=weights)[0]

            return int(row.index[val])
        except KeyError:
            return -1
