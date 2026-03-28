from engine.plugins.base_plugin import BasePlugin


class Plugin(BasePlugin):
    manifest_id = "youtube_script"
    title = "YouTube Script"
    description = "Outline a spoken script with hook, sections, and CTA."

    def build_prompt(self, user_input: str) -> str:
        return (
            "You are a YouTube scriptwriter. Produce a spoken script with: hook, main sections, and outro CTA.\n\n"
            f"Topic / notes:\n{user_input.strip()}\n\n"
            "Script:"
        )
