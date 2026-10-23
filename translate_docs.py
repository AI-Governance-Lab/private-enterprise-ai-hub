#!/usr/bin/env python3
"""
Enterprise Documentation Multilingual Translation Tool (EN, RO, FR)
Translates Markdown files while preserving code blocks and Markdown syntax.
"""

import sys
import os
import re
import json
import time
import urllib.request
from pathlib import Path

LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000/v1/chat/completions")
MODEL_NAME = os.getenv("TRANSLATE_MODEL", "Gemini 3.8 Flash")

LANG_NAMES = {
    "en": "English",
    "ro": "Romanian (Limba Română)",
    "fr": "French (Français)",
}

INTERNAL_DOCS = [
    "README",
    "CAD_README",
    "litellm",
    "cline_config_gcp_login",
]

def extract_code_blocks(text: str) -> tuple[str, list[str]]:
    pattern = re.compile(r'(```[\s\S]*?```)', re.MULTILINE)
    blocks = []
    def replacer(m):
        idx = len(blocks)
        blocks.append(m.group(1))
        return f"\n<<<CODE_BLOCK_{idx}>>>\n"
    return pattern.sub(replacer, text), blocks

def restore_code_blocks(text: str, blocks: list[str]) -> str:
    res = text
    for i, b in enumerate(blocks):
        res = res.replace(f"<<<CODE_BLOCK_{i}>>>", b)
    return res

def strip_existing_lang_header(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines:
        return text
    first = lines[0].strip()
    if ("[English]" in first or "[Română]" in first) and "|" in first:
        idx = 1
        while idx < len(lines) and (lines[idx].strip() == "" or lines[idx].strip() == "---"):
            idx += 1
        return "".join(lines[idx:])
    return text

def make_lang_header(base_name: str) -> str:
    return f"[English]({base_name}.md) | [Română]({base_name}.ro.md) | [Français]({base_name}.fr.md)\n\n---\n\n"

def split_into_chunks(text: str, max_chunk_len: int = 3500) -> list[str]:
    section_pattern = re.compile(r'(?=\n#{1,3}\s+)', re.MULTILINE)
    raw_sections = section_pattern.split(text)
    chunks, cur, cur_len = [], [], 0
    for sec in raw_sections:
        if not sec:
            continue
        if len(sec) > max_chunk_len:
            for p in sec.split("\n\n"):
                if cur_len + len(p) + 2 > max_chunk_len and cur:
                    chunks.append("".join(cur))
                    cur, cur_len = [p + "\n\n"], len(p) + 2
                else:
                    cur.append(p + "\n\n")
                    cur_len += len(p) + 2
        else:
            if cur_len + len(sec) > max_chunk_len and cur:
                chunks.append("".join(cur))
                cur, cur_len = [sec], len(sec)
            else:
                cur.append(sec)
                cur_len += len(sec)
    if cur:
        chunks.append("".join(cur))
    return chunks

def call_litellm_translate(text: str, source_lang: str, target_lang: str) -> str:
    if not text.strip():
        return text
    cleaned = re.sub(r'<<<CODE_BLOCK_\d+>>>', '', text).strip()
    if not cleaned:
        return text

    target_name = LANG_NAMES.get(target_lang, target_lang)
    source_name = LANG_NAMES.get(source_lang, source_lang)
    system_prompt = (
        f"You are a professional technical translator for an Enterprise AI Hub project.\n"
        f"Translate the following Markdown documentation from {source_name} to {target_name}.\n"
        f"RULES:\n"
        f"1. Preserve ALL Markdown formatting syntax exact (#, ##, **, *, |, -, `, etc.).\n"
        f"2. CRITICAL: NEVER translate, modify or delete <<<CODE_BLOCK_X>>> placeholders.\n"
        f"3. Keep technical terms, Docker/bash commands, file paths, and model names in English.\n"
        f"4. For tables (| col1 | col2 |), keep structure and column alignments.\n"
        f"5. Return ONLY translated Markdown text, with no preamble or outer code blocks."
    )
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Text to translate:\n\n{text}"}
        ],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        LITELLM_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer dummy"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                if content.startswith("```markdown\n") and content.endswith("\n```"):
                    content = content[12:-4]
                elif content.startswith("```\n") and content.endswith("\n```"):
                    content = content[4:-4]
                return content
        except Exception as e:
            print(f"    [!] Error (attempt {attempt+1}/3): {e}", file=sys.stderr)
def adapt_links(text: str, target_lang: str) -> str:
    if target_lang == "ro":
        for doc in INTERNAL_DOCS:
            text = re.sub(rf'\((\.\./)?{re.escape(doc)}\.md(#.*?)?\)', rf'(\1{doc}.ro.md\2)', text)
            text = re.sub(rf'\((\.\./)?{re.escape(doc)}\.fr\.md(#.*?)?\)', rf'(\1{doc}.ro.md\2)', text)
    elif target_lang == "fr":
        for doc in INTERNAL_DOCS:
            text = re.sub(rf'\((\.\./)?{re.escape(doc)}\.md(#.*?)?\)', rf'(\1{doc}.fr.md\2)', text)
            text = re.sub(rf'\((\.\./)?{re.escape(doc)}\.ro\.md(#.*?)?\)', rf'(\1{doc}.fr.md\2)', text)
    elif target_lang == "en":
        for doc in INTERNAL_DOCS:
            text = re.sub(rf'\((\.\./)?{re.escape(doc)}\.(ro|fr)\.md(#.*?)?\)', rf'(\1{doc}.md\3)', text)
    return text

def translate_file(input_path: Path, output_path: Path, source_lang: str, target_lang: str) -> None:
    print(f"\n📄 {input_path.name} ({source_lang.upper()}) -> {output_path.name} ({target_lang.upper()})")
    with open(input_path, "r", encoding="utf-8") as f:
        original = f.read()

    base_name = re.sub(r'\.(ro|fr)\.md$', '', output_path.name)
    base_name = re.sub(r'\.md$', '', base_name)

    body = strip_existing_lang_header(original)
    body_no_code, code_blocks = extract_code_blocks(body)
    chunks = split_into_chunks(body_no_code)

    translated_chunks = []
    for i, c in enumerate(chunks, 1):
        print(f"  [{i}/{len(chunks)}] translating...", end="", flush=True)
        t0 = time.time()
        res = call_litellm_translate(c, source_lang, target_lang)
        print(f" done ({time.time()-t0:.1f}s)")
        translated_chunks.append(res)

    full = "".join(translated_chunks)
    restored = restore_code_blocks(full, code_blocks)
    adapted = adapt_links(restored, target_lang)
    final_content = make_lang_header(base_name) + adapted.lstrip()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp = output_path.with_suffix(".tmp")
    with open(temp, "w", encoding="utf-8") as f:
        f.write(final_content)
    temp.replace(output_path)
    print(f"  ✓ Saved {output_path} ({len(final_content)} bytes)")

def update_header_only(file_path: Path, target_lang: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    base_name = re.sub(r'\.(ro|fr)\.md$', '', file_path.name)
    base_name = re.sub(r'\.md$', '', base_name)
    body = strip_existing_lang_header(content)
    adapted = adapt_links(body, target_lang)
    final_content = make_lang_header(base_name) + adapted.lstrip()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"  ✓ Header updated: {file_path}")

def run_all():
    root = Path(__file__).resolve().parent
    vscode_ro = root / "vscode.ro.md"
    if not vscode_ro.exists() and (root / "vscode.md").exists():
        vscode_ro.write_text((root / "vscode.md").read_text(encoding="utf-8"), encoding="utf-8")

    tasks = [
        {"in": root / "README.md", "out": root / "README.ro.md", "src": "en", "tgt": "ro"},
        {"in": root / "README.md", "out": root / "README.fr.md", "src": "en", "tgt": "fr"},
        {"in": root / "litellm.md", "out": root / "litellm.ro.md", "src": "en", "tgt": "ro"},
        {"in": root / "litellm.md", "out": root / "litellm.fr.md", "src": "en", "tgt": "fr"},
        {"in": root / "CAD_README.ro.md", "out": root / "CAD_README.md", "src": "ro", "tgt": "en"},
        {"in": root / "CAD_README.ro.md", "out": root / "CAD_README.fr.md", "src": "ro", "tgt": "fr"},
        {"in": vscode_ro, "out": root / "vscode.md", "src": "ro", "tgt": "en"},
        {"in": vscode_ro, "out": root / "vscode.fr.md", "src": "ro", "tgt": "fr"},
        {"in": root / "cline_config_gcp_login.ro.md", "out": root / "cline_config_gcp_login.md", "src": "ro", "tgt": "en"},
        {"in": root / "cline_config_gcp_login.ro.md", "out": root / "cline_config_gcp_login.fr.md", "src": "ro", "tgt": "fr"},
        {"in": root / "cad-service/samples/README.ro.md", "out": root / "cad-service/samples/README.md", "src": "ro", "tgt": "en"},
        {"in": root / "cad-service/samples/README.ro.md", "out": root / "cad-service/samples/README.fr.md", "src": "ro", "tgt": "fr"},
    ]
    print("Pre-updating headers on source files...")
    for src_path, lang in [
        (root / "README.md", "en"),
        (root / "litellm.md", "en"),
        (root / "CAD_README.ro.md", "ro"),
        (vscode_ro, "ro"),
        (root / "cline_config_gcp_login.ro.md", "ro"),
        (root / "cad-service/samples/README.ro.md", "ro"),
    ]:
        if src_path.exists():
            update_header_only(src_path, lang)

    for t in tasks:
        if t["in"].exists():
            translate_file(t["in"], t["out"], t["src"], t["tgt"])

if __name__ == "__main__":
    if len(sys.argv) == 1 or "--all" in sys.argv:
        run_all()
    elif len(sys.argv) == 5:
        translate_file(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4])

