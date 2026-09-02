class DefaultDocumentationPromptBuilder:
    """Build a compact JSON documentation prompt."""

    def build(self, context: str) -> str:
        return f"""
Analisis SOURCE ANALYSIS berikut.

Kembalikan HANYA JSON valid.
Gunakan Bahasa Indonesia untuk deskripsi.
Jangan gunakan Markdown.
Jangan gunakan ```json.
Jangan menambahkan teks di luar JSON.
Gunakan hanya informasi yang tersedia.
Jangan mengarang informasi.
Gunakan null jika informasi tidak tersedia.
Gunakan [] jika kosong.
Buat semua deskripsi singkat.

FORMAT JSON:

{{
  "module": {{
    "name": "",
    "description": null
  }},
  "imports": [],
  "functions": [],
  "classes": [],
  "technical_notes": []
}}

FUNCTION:
{{
  "name": "",
  "description": null,
  "parameters": [],
  "return_type": null,
  "return_description": null,
  "decorators": [],
  "async": false
}}

PARAMETER:
{{
  "name": "",
  "type": null,
  "default": null,
  "description": null
}}

CLASS:
{{
  "name": "",
  "description": null,
  "decorators": [],
  "methods": []
}}

METHOD menggunakan format yang sama seperti FUNCTION.

SOURCE ANALYSIS:
{context}
""".strip()