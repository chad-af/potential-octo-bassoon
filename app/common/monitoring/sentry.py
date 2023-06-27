import sentry_sdk

from typing import Optional

from sentry_sdk import Scope


class ErrorForm:
    ERROR = "error"
    TAGS = "tags"
    CONTEXT = "context"

    class ContextForm:
        name: str
        content: Optional[dict]

        def __init__(self, name, content=None):
            self.name = name
            self.content = content

    error: Exception
    tags: Optional[dict[str, str]]
    context: Optional[ContextForm]

    def __init__(
        self,
        error,
        tags: Optional[dict[str, str]] = None,
        context: Optional[ContextForm] = None,
    ):
        self.error = error
        self.tags = tags
        self.context = context


def report_exception(
    error,
    context_name: str = None,
    context_content: dict = None,
    tags: dict[str, str] = None,
):
    request_body = ErrorForm(error=error)
    if context_name:
        request_body.context = ErrorForm.ContextForm(
            name=context_name, content=context_content
        )
    request_body.tags = tags
    report_exception_with_form(request_body)


def report_exception_with_form(request_body: ErrorForm):
    if request_body.context:
        sentry_sdk.set_context(request_body.context.name, request_body.context.content)

    with sentry_sdk.push_scope() as scope:
        set_tags_for_active_scope(request_body, scope)
        sentry_sdk.capture_exception(request_body.error)


def set_tags_for_active_scope(request_body: ErrorForm, scope: Scope):
    if not request_body.tags:
        return

    for key, value in request_body.tags.items():
        scope.set_tag(key, value)
