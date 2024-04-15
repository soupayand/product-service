from contextvars import ContextVar

user_info_context : ContextVar[dict] = ContextVar("user_info_context")
