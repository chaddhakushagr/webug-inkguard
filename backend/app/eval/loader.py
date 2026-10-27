"""
Dataset loader for Inkguard evaluation benchmark documents.
Discovers and loads all *.json documents from backend/app/eval/dataset/.
"""

import os
import glob
import json
from typing import List, Optional
from app.eval.schema import EvalDocument


DEFAULT_DATASET_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "dataset")
)


def load_dataset(dataset_dir: Optional[str] = None) -> List[EvalDocument]:
    """
    Loads all JSON evaluation documents from dataset_dir sorted by document ID.
    Raises ValueError on invalid files or missing fields.
    """
    target_dir = dataset_dir or DEFAULT_DATASET_DIR
    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f"Evaluation dataset directory not found: {target_dir}")

    json_files = sorted(glob.glob(os.path.join(target_dir, "*.json")))
    if not json_files:
        raise ValueError(f"No JSON benchmark files found in: {target_dir}")

    docs: List[EvalDocument] = []
    seen_ids = set()

    for path in json_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to read evaluation file '{path}': {e}") from e

        # Support single document dict or list of documents in one file
        items = data if isinstance(data, list) else [data]
        for item in items:
            doc = EvalDocument.from_dict(item)
            if doc.id in seen_ids:
                raise ValueError(f"Duplicate document id '{doc.id}' found in '{path}'")
            seen_ids.add(doc.id)
            docs.append(doc)

    docs.sort(key=lambda d: d.id)
    return docs
