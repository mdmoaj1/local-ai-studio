from engine.plugins.base_plugin import BasePlugin


class Plugin(BasePlugin):
    manifest_id = "content_generator"
    title = "Content Generator"
    description = "Turn a short brief into polished marketing or product copy."

    def build_prompt(self, user_input: str) -> str:
        return (
            "You are an expert copywriter. Write concise, engaging content.\n\n"
            f"Brief:\n{user_input.strip()}\n\n"
            "Output:"
        )
