"""Resolve the pinned content digest of the local Ollama embedder, so evidence
bundles record WHICH embedder produced their retrieval traces (not just the mutable
`latest` tag). Best-effort: returns None digests if the manifest cannot be found."""
from __future__ import annotations

import glob
import json
import os
from typing import Dict, Optional

_MANIFEST_BASES = (
    os.path.expanduser("~/.ollama"),
    "/usr/share/ollama/.ollama",
    "/root/.ollama",
)


def resolve_embed_digest(model_tag: str = "nomic-embed-text:latest") -> Dict[str, Optional[str]]:
    """Return {'model_layer','config','manifest','tag'} for the embedder model.

    model_layer = sha256 of the weights layer (authoritative content id);
    config = manifest config digest; manifest = path used. Robust to the tag's
    ':latest' suffix and to Ollama's shared-store location under /usr/share."""
    name = model_tag.split(":")[0]
    variant = model_tag.split(":")[1] if ":" in model_tag else "latest"
    for base in _MANIFEST_BASES:
        for m in glob.glob(base + f"/models/manifests/**/{name}/{variant}", recursive=True):
            if os.path.isfile(m):
                try:
                    man = json.load(open(m))
                except (OSError, ValueError):
                    continue
                model_layer = next((l.get("digest") for l in man.get("layers", [])
                                    if str(l.get("mediaType", "")).endswith("image.model")), None)
                return {"tag": model_tag, "model_layer": model_layer,
                        "config": man.get("config", {}).get("digest"), "manifest": m}
    return {"tag": model_tag, "model_layer": None, "config": None, "manifest": None}
