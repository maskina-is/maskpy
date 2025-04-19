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

def parse_variable_labels(txt: str, types: dict, groups: dict):
    """Returns variable_labels and value_labels dicts"""
    variable_labels = {}
    value_labels = {}

    for line in txt.splitlines():
        match = re.match(r"label (\w+)\s*=\s*'(.*?)'", line)
        if match:
            varname, label = match.groups()

            if varname in types and types[varname] == "single":
                variable_labels[varname] = label
            else:
                # subvar from a multi group
                for main_var, subvars in groups.items():
                    if varname in subvars.values():
                        # Try splitting label like "Main – Option"
                        if "–" in label:
                            question, value = map(str.strip, label.split("–", 1))
                        elif "-" in label:
                            question, value = map(str.strip, label.split("-", 1))
                        else:
                            question, value = label, label

                        variable_labels[main_var] = question
                        code = [k for k, v in subvars.items() if v == varname][0]
                        value_labels.setdefault(main_var, {})[code] = value
    return variable_labels, value_labels

def build_metadata(types: dict, groups: dict, variable_labels: dict, value_labels: dict):
    metadata = {}

    for var, vtype in types.items():
        entry = {
            "type": vtype,
            "variable_label": variable_labels.get(var),
        }

        if vtype == "multi":
            entry["subvars"] = groups.get(var, {})
            entry["value_labels"] = value_labels.get(var, {})
        else:
            entry["value_labels"] = value_labels.get(var, {})

        metadata[var] = entry

    return metadata
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

def read_metadata(filepath: str):
    with open(filepath, encoding="utf-8") as f:
        txt = f.read()

    types, groups = parse_variable_types(txt)
    var_labels, val_labels = parse_variable_labels(txt, types, groups)
    metadata = build_metadata(types, groups, var_labels, val_labels)
    return metadata

def load_labeled_data(data_path: str, metadata_path: str):
    df = read_survey_data(data_path)
    metadata = read_metadata(metadata_path)
    df = expand_multiple_response_columns(df, metadata)
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

def parse_variable_types(txt: str):
    """Returns:
    - types: {varname: "multi"|"single"}
    - groups: {groupname: {code: varname}} for multi-response questions
    """
    types = {}
    groups = defaultdict(dict)

    for line in txt.splitlines():
        if line.strip().startswith("format"):
            parts = line.strip().split()
            var = parts[1]
            fmt = parts[2].rstrip(".;")

            if fmt.startswith("Multi_"):
                main_var = fmt.replace("Multi_", "")
                types[main_var] = "multi"
                match = re.search(r"_(\d+)$", var)
                if match:
                    code = int(match.group(1))
                    groups[main_var][code] = var
            else:
                types[var] = "single"
    return types, dict(groups)

def expand_multiple_response_columns(df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    df = df.copy()
    for var, info in metadata.items():
        if info["type"] == "multi" and var in df.columns:
            binary_series = df[var].fillna("").astype(str)
            for code, subvar in info["subvars"].items():
                df[subvar] = binary_series.str.pad(len(info["subvars"]), fillchar="0").str[code - 1].astype(int)
            df.drop(columns=[var], inplace=True)
    return df
