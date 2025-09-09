#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Leer archivo
with open('src/db_auditor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar emojis
replacements = {
    '⚠️': 'WARNING:',
    '✅': 'OK:',
    'ℹ️': 'INFO:',
    '❌': 'ERROR:',
    '🔍': 'AUDIT:',
    '📄': 'REPORT:',
    '🎉': 'SUCCESS:'
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Escribir archivo corregido
with open('src/db_auditor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Emojis reemplazados exitosamente")