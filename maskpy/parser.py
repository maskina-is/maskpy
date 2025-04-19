import pandas as pd
import re
from collections import defaultdict
from .labeled_df import LabeledDataFrame

def read_survey_data(filepath: str) -> pd.DataFrame:
    return pd.read_excel(filepath, engine="openpyxl")

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

def build_metadata(value_labels: dict, variable_labels: dict, variable_types: dict) -> dict:
    metadata = {}
    grouped = defaultdict(dict)

    # Collect subvariables for each multi group
    for var, (vtype, group) in variable_types.items():
        if vtype == "multi" and group:
            # Extract value position from variable name (e.g., BIL10_3 → 3)
            match = re.search(r"_(\d+)$", var)
            if match:
                value_code = int(match.group(1))
                grouped[group][value_code] = var

    all_vars = set(value_labels) | set(variable_labels) | set(variable_types)

    for var in all_vars:
        vtype, group = variable_types.get(var, ("single", None))

        # Skip subvars – they'll be represented by the parent multi variable
        if vtype == "multi" and group and var != group:
            continue

        entry = {
            "type": vtype,
            "variable_label": variable_labels.get(var),
            "value_labels": value_labels.get(var),
        }

        if vtype == "multi":
            entry["subvars"] = grouped.get(var, {})

        metadata[var] = entry

    return metadata

def read_metadata(filepath: str) -> dict:
    with open(filepath, encoding='utf-8') as f:
        txt = f.read()

    value_labels = parse_value_labels(txt)
    variable_labels = parse_variable_labels(txt)
    variable_types = parse_format_blocks(txt)

    return build_metadata(value_labels, variable_labels, variable_types)

def load_labeled_data(data_path: str, metadata_path: str):
    df = read_survey_data(data_path)
    metadata = read_metadata(metadata_path)
    return LabeledDataFrame(df, metadata)

def parse_format_blocks(txt: str) -> dict:
    """
    Parses format lines like:
    format BIL10_1 Multi_BIL10.;
    Returns a dict: {varname: ("multi", "BIL10")} or {varname: ("single", None)}
    """
    types = {}
    for line in txt.splitlines():
        if line.strip().startswith("format"):
            parts = line.strip().split()
            if len(parts) >= 3:
                var = parts[1]
                fmt = parts[2].rstrip(".;")
                if fmt.startswith("Multi_"):
                    group = fmt.replace("Multi_", "")
                    types[var] = ("multi", group)
                else:
                    types[var] = ("single", None)
    return types
