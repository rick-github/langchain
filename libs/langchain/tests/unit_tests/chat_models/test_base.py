import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from langchain.chat_models.base import __all__, init_chat_model

EXPECTED_ALL = [
    "BaseChatModel",
    "SimpleChatModel",
    "agenerate_from_stream",
    "generate_from_stream",
    "init_chat_model",
]


def test_all_imports() -> None:
    assert set(__all__) == set(EXPECTED_ALL)


@pytest.mark.requires(
    "langchain_openai",
    "langchain_anthropic",
    "langchain_fireworks",
    "langchain_together",
    "langchain_mistralai",
    "langchain_groq",
)
@pytest.mark.parametrize(
    ["model_name", "model_provider"],
    [
        ("gpt-4o", "openai"),
        ("claude-3-opus-20240229", "anthropic"),
        ("accounts/fireworks/models/mixtral-8x7b-instruct", "fireworks"),
        ("meta-llama/Llama-3-8b-chat-hf", "together"),
        ("mixtral-8x7b-32768", "groq"),
    ],
)
def test_init_chat_model(model_name: str, model_provider: str) -> None:
    _: BaseChatModel = init_chat_model(
        model_name, model_provider=model_provider, api_key="foo"
    )


def test_init_missing_dep() -> None:
    with pytest.raises(ImportError):
        init_chat_model("mixtral-8x7b-32768", model_provider="groq")


def test_init_unknown_provider() -> None:
    with pytest.raises(ValueError):
        init_chat_model("foo", model_provider="bar")


@pytest.mark.requires("langchain_openai")
def test_configurable() -> None:
    model = init_chat_model()

    for method in (
        "invoke",
        "ainvoke",
        "batch",
        "abatch",
        "stream",
        "astream",
        "batch_as_completed",
        "abatch_as_completed",
    ):
        assert hasattr(model, method)

    # Doesn't have access non-configurable, non-declarative methods until a config is
    # provided.
    for method in ("get_num_tokens", "get_num_tokens_from_messages", "dict"):
        with pytest.raises(AttributeError):
            getattr(model, method)

    # Can call declarative methods even without a default model.
    model_with_tools = model.bind_tools(
        [{"name": "foo", "description": "foo", "parameters": {}}]
    )

    # Can iteratively call declarative methods.
    model_with_config = model_with_tools.with_config(
        RunnableConfig(tags=["foo"]), configurable={"model": "gpt-4o"}
    )

    # with_config has special handling to extract model params, so that we now have a
    # default model. meaning we can access non-configurable, non-declarative methods as
    # well.
    assert model_with_config.get_num_tokens_from_messages([(HumanMessage("foo"))]) == 8


@pytest.mark.requires("langchain_openai", "langchain_anthropic")
def test_configurable_with_default() -> None:
    model = init_chat_model("gpt-4o", config_prefix="")
    for method in (
        "invoke",
        "ainvoke",
        "batch",
        "abatch",
        "stream",
        "astream",
        "batch_as_completed",
        "abatch_as_completed",
    ):
        assert hasattr(model, method)

    # Does have access non-configurable, non-declarative methods since default params
    # are provided.
    for method in ("get_num_tokens", "get_num_tokens_from_messages", "dict"):
        assert hasattr(model, method)

    model_with_tools = model.bind_tools(
        [{"name": "foo", "description": "foo", "parameters": {}}]
    )

    model_with_config = model_with_tools.with_config(
        RunnableConfig(tags=["foo"]), configurable={"model": "claude-3-sonnet-20240229"}
    )

    assert model.get_num_tokens_from_messages([(HumanMessage("foo"))]) == 8

    # Anthropic defaults to using `transformers` for token counting.
    with pytest.raises(ImportError):
        model_with_config.get_num_tokens_from_messages([(HumanMessage("foo"))])
