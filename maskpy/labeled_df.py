import pandas as pd

class LabeledDataFrame:
    def __init__(self, data: pd.DataFrame, metadata: dict):
        self.data = data
        self.metadata = metadata

    def get_variable_label(self, column: str):
        return self.metadata.get(column, {}).get("variable_label")

    def get_value_labels(self, column: str):
        return self.metadata.get(column, {}).get("value_labels")

    def __getitem__(self, key):
        return self.data[key]

    def __repr__(self):
        return f"LabeledDataFrame({len(self.data)} rows, {len(self.data.columns)} cols)"
   
    def set_variable_label(self, column: str, label: str):
        """Set or update the variable label for a given column."""
        if column not in self.data.columns:
            raise KeyError(f"Column '{column}' not found in data.")
        if column not in self.metadata:
            self.metadata[column] = {}
        self.metadata[column]["variable_label"] = label
