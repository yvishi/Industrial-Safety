from app.ai.context.schemas import AIContext
from app.ai.prompts.templates import get_template
from app.ai.providers.base import AIGenerationResult, AIProvider


class AIService:
    """
    Orchestrates the three AI Foundation building blocks — a PromptTemplate, an AIContext from
    the Context Builder, and an AIProvider — into one generation call.

    Deliberately has no capability-specific methods (no `explain_incident()`,
    `summarize_report()`, ...): every future capability is the same call shape,
    `generate(template_id, context, **template_vars)`, against a different template and a
    differently-scoped context. Adding a capability later means a new call site (and, if
    needed, a new ContextBuilder method or prompt template) — never new architecture here.
    """

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def generate(
        self,
        *,
        template_id: str,
        context: AIContext | None = None,
        **template_vars: str,
    ) -> AIGenerationResult:
        template = get_template(template_id)
        prompt = template.render(
            context=context.as_prompt_text() if context is not None else "",
            **template_vars,
        )
        return await self.provider.generate(prompt=prompt, system_prompt=template.system_prompt)
