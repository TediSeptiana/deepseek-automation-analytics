from __future__ import annotations

import json
from typing import Any


class MarkdownRenderer:
    """Render JSON documentation string menjadi Markdown."""

    def render(self, content: str) -> str:
        if not isinstance(content, str):
            raise TypeError("Renderer menerima content berupa string.")

        content = content.strip()

        # Bersihkan code fence jika LLM tetap mengirimkannya
        if content.startswith("```"):
            lines = content.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        # Parse JSON dari string response LLM
        try:
            data: dict[str, Any] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM menghasilkan JSON tidak valid: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError("Root JSON harus berupa object.")

        lines: list[str] = []

        # Module
        module = data.get("module", {})

        if isinstance(module, dict):
            name = module.get("name", "Unknown Module")
            description = module.get("description")

            lines.append(f"# {name}")
            lines.append("")

            if description:
                lines.append(str(description))
                lines.append("")

        # Imports
        imports = data.get("imports", [])

        if imports:
            lines.append("## Imports")
            lines.append("")

            for item in imports:
                if isinstance(item, str):
                    lines.append(f"- `{item}`")

                elif isinstance(item, dict):
                    name = item.get("name", "")
                    import_type = item.get("type")

                    if import_type:
                        lines.append(f"- `{name}` — {import_type}")
                    else:
                        lines.append(f"- `{name}`")

            lines.append("")

        # Functions
        functions = data.get("functions", [])

        if functions:
            lines.append("## Functions")
            lines.append("")

            for function in functions:
                if not isinstance(function, dict):
                    continue

                name = function.get("name", "")
                description = function.get("description")

                lines.append(f"### `{name}()`")
                lines.append("")

                if description:
                    lines.append(str(description))
                    lines.append("")

                parameters = function.get("parameters", [])

                if isinstance(parameters, list) and parameters:
                    lines.append("**Parameters:**")
                    lines.append("")

                    for parameter in parameters:
                        if not isinstance(parameter, dict):
                            continue

                        param_name = parameter.get("name", "")
                        param_type = parameter.get("type")
                        default = parameter.get("default")

                        text = f"- `{param_name}`"

                        if param_type is not None:
                            text += f": `{param_type}`"

                        if default is not None:
                            text += f" = `{default}`"

                        lines.append(text)

                    lines.append("")

                return_type = function.get("return_type")

                if return_type is not None:
                    lines.append(f"**Returns:** `{return_type}`")
                    lines.append("")

        # Classes
        classes = data.get("classes", [])

        if classes:
            lines.append("## Classes")
            lines.append("")

            for cls in classes:
                if not isinstance(cls, dict):
                    continue

                class_name = cls.get("name", "")
                description = cls.get("description")

                lines.append(f"### `{class_name}`")
                lines.append("")

                if description:
                    lines.append(str(description))
                    lines.append("")

                methods = cls.get("methods", [])

                if methods:
                    lines.append("#### Methods")
                    lines.append("")

                    for method in methods:
                        if not isinstance(method, dict):
                            continue

                        method_name = method.get("name", "")
                        method_description = method.get("description")

                        lines.append(f"##### `{method_name}()`")
                        lines.append("")

                        if method_description:
                            lines.append(str(method_description))
                            lines.append("")

                        parameters = method.get("parameters", [])

                        if parameters:
                            lines.append("**Parameters:**")
                            lines.append("")

                            for parameter in parameters:
                                if not isinstance(parameter, dict):
                                    continue

                                param_name = parameter.get("name", "")
                                param_type = parameter.get("type")
                                default = parameter.get("default")

                                text = f"- `{param_name}`"

                                if param_type is not None:
                                    text += f": `{param_type}`"

                                if default is not None:
                                    text += f" = `{default}`"

                                lines.append(text)

                            lines.append("")

                        return_type = method.get("return_type")

                        if return_type is not None:
                            lines.append(f"**Returns:** `{return_type}`")
                            lines.append("")

        # Technical notes
        technical_notes = data.get("technical_notes", [])

        if technical_notes:
            lines.append("## Technical Notes")
            lines.append("")

            for note in technical_notes:
                lines.append(f"- {note}")

            lines.append("")

        return "\n".join(lines).strip() + "\n"