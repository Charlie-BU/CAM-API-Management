# 版本号转换为数字，如1.0.0 -> 100
from typing import List


def version2Number(version_str: str) -> int:
    try:
        parts = version_str.split(".")
        if len(parts) == 3:
            major, minor, patch = parts
            return int(major) * 100 + int(minor) * 10 + int(patch)
        return 0
    except (ValueError, AttributeError):
        return 0


def string2Bool(str: str) -> bool:
    return str.lower() == "true"