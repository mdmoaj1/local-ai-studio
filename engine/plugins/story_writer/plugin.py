from engine.plugins.base_plugin import BasePlugin


class Plugin(BasePlugin):
    manifest_id = "story_writer"
    title = "Story Writer"
    description = "Short fiction from a premise or outline."

    def build_prompt(self, user_input: str) -> str:
        return (
            "You are a fiction writer. Write a cohesive short story.\n\n"
            f"Premise:\n{user_input.strip()}\n\n"
            "Story:"
        )
