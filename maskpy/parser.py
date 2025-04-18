import pandas as pd
import re
from collections import defaultdict

def read_survey_data(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath, sep=';', encoding='utf-8', quotechar='"')

def parse_value_labels(txt: str) -> dict:
    value_labels = defaultdict(dict)
    current_var = None

    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("value"):
            current_var = line.split()[1]
        elif "=" in line and current_var:
            match = re.match(r"(\d+)\s*=\s*'(.*?)'", line)
            if match:
                code, label = match.groups()
                value_labels[current_var][int(code)] = label
        elif line == ";":
            current_var = None
    return dict(value_labels)

def parse_variable_labels(txt: str) -> dict:
    variable_labels = {}

    for line in txt.splitlines():
        if line.startswith("label "):
            match = re.match(r"label (\w+) = '(.*?)'", line)
            if match:
                var, label = match.groups()
                variable_labels[var] = label
    return variable_labels

 def build_metadata(value_labels: dict, variable_labels: dict) -> dict:
    metadata = {}
    all_vars = set(value_labels) | set(variable_labels)

    for var in all_vars:
        metadata[var] = {
            "value_labels": value_labels.get(var),
            "variable_label": variable_labels.get(var)
        }
    return metadata

def read_metadata(filepath: str) -> dict:
    with open(filepath, encoding='utf-8') as f:
        txt = f.read()
    
    value_labels = parse_value_labels(txt)
    variable_labels = parse_variable_labels(txt)
    return build_metadata(value_labels, variable_labels)

def load_labeled_data(data_path: str, metadata_path: str):
    df = read_survey_data(data_path)
    metadata = read_metadata(metadata_path)
    return LabeledDataFrame(df, metadata)

