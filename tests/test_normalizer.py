"""Tests for driftwatch.normalizer."""
import pytest
from driftwatch.normalizer import NormalizeOptions, NormalizerError, normalize_config


def test_lowercase_keys():
    result = normalize_config({"FOO": 1, "Bar": 2})
    assert "foo" in result
    assert "bar" in result


def test_strip_string_values():
    result = normalize_config({"key": "  hello  "})
    assert result["key"] == "hello"


def test_coerce_boolean_true_variants():
    for val in ("true", "yes", "1", "on", "True", "YES"):
        result = normalize_config({"flag": val})
        assert result["flag"] is True, f"Expected True for {val!r}"


def test_coerce_boolean_false_variants():
    for val in ("false", "no", "0", "off"):
        result = normalize_config({"flag": val})
        assert result["flag"] is False, f"Expected False for {val!r}"


def test_non_boolean_string_unchanged():
    result = normalize_config({"name": "production"})
    assert result["name"] == "production"


def test_remove_none_values():
    opts = NormalizeOptions(remove_none_values=True)
    result = normalize_config({"a": 1, "b": None}, opts)
    assert "b" not in result
    assert result["a"] == 1


def test_none_values_kept_by_default():
    result = normalize_config({"a": None})
    assert "a" in result
    assert result["a"] is None


def test_nested_dict_normalized():
    result = normalize_config({"DB": {"HOST": "  localhost  ", "PORT": "true"}})
    assert "db" in result
    assert result["db"]["host"] == "localhost"
    assert result["db"]["port"] is True


def test_list_values_normalized():
    result = normalize_config({"flags": ["true", "false", "  hello  "]})
    assert result["flags"] == [True, False, "hello"]


def test_ignored_keys_not_normalized():
    opts = NormalizeOptions(ignored_keys=["raw"])
    result = normalize_config({"RAW": "  value  "}, opts)
    assert result["raw"] == "  value  "


def test_raises_on_non_dict_input():
    with pytest.raises(NormalizerError):
        normalize_config(["not", "a", "dict"])  # type: ignore


def test_disable_lowercase_keys():
    opts = NormalizeOptions(lowercase_keys=False)
    result = normalize_config({"FOO": "bar"}, opts)
    assert "FOO" in result
    assert "foo" not in result
