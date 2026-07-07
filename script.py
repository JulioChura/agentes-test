import os
import sys

# ================= CONFIGURACIÓN =================
# Directorios a ignorar (nombres exactos)
IGNORE_DIRS = [
    '.venv', 'venv', 'env', 'ENV', 'virtualenv',
    '__pycache__', '.git', '.idea', '.vscode',
    'node_modules', 'dist', 'build', 'target',
    'logs', 'log', 'temp', 'tmp'
]

# Extensiones de archivos a ignorar (incluir el punto, en minúscula)
IGNORE_EXTS = [
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe',
    '.class', '.jar', '.war', '.ear',
    '.db', '.sqlite', '.sqlite3',
    '.log', '.cache', '.tmp', '.temp',
    '.o', '.obj', '.pdb', '.idb', '.pch',
    '.psd', '.ai', '.pdf', '.zip', '.rar', '.7z',
    '.mp4', '.avi', '.mov', '.mkv',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
    '.mp3', '.wav', '.flac'
]

# Tamaño máximo de archivo a incluir (bytes) – 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# ================= FUNCIONES AUXILIARES =================
def should_ignore_dir(dirname):
    """Determina si un directorio debe ser ignorado"""
    if dirname.startswith('.'):
        return True
    return dirname in IGNORE_DIRS

def should_ignore_file(filename):
    """Determina si un archivo debe ser ignorado"""
    if filename.startswith('.'):
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in IGNORE_EXTS

def get_file_language(filename):
    """Devuelve el lenguaje para el bloque de código Markdown según la extensión"""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text',
        '.sh': 'bash',
        '.bat': 'batch',
        '.ps1': 'powershell',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'cpp',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.sql': 'sql',
        '.r': 'r',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.dart': 'dart',
        '.lua': 'lua',
        '.pl': 'perl',
        '.pm': 'perl',
    }
    return mapping.get(ext, '')

# ================= GENERADOR PRINCIPAL =================
def generate_readme(root_dir='.', output_file='README.md'):
    """Recorre el directorio y escribe un README con todos los archivos"""

    all_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Podar directorios ignorados (modificación in-place)
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]

        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == '.':
            rel_dir = ''

        for filename in filenames:
            if should_ignore_file(filename):
                continue

            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.join(rel_dir, filename) if rel_dir else filename

            # Saltar archivos demasiado grandes
            try:
                size = os.path.getsize(full_path)
                if size > MAX_FILE_SIZE:
                    print(f"⚠️  Saltando {rel_path} (tamaño: {size} bytes)")
                    continue
            except OSError:
                continue

            # Intentar leer como texto UTF-8
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                print(f"⚠️  Saltando {rel_path} (no es texto UTF-8)")
                continue
            except Exception as e:
                print(f"⚠️  Error al leer {rel_path}: {e}")
                continue

            all_files.append((rel_path, content))

    # Ordenar alfabéticamente
    all_files.sort(key=lambda x: x[0])

    # Construir contenido del README
    lines = []
    lines.append("# 📁 Contenido completo del proyecto")
    lines.append("")
    lines.append(f"**Total de archivos incluidos:** {len(all_files)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for file_path, content in all_files:
        lang = get_file_language(file_path)
        lines.append(f"## `{file_path}`")
        lines.append("")
        lines.append(f"```{lang}")
        lines.append(content)
        if content and not content.endswith('\n'):
            lines.append('')  # Asegurar nueva línea final
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Escribir archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ README generado: {output_file} con {len(all_files)} archivos.")

# ================= PUNTO DE ENTRADA =================
if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    output = sys.argv[2] if len(sys.argv) > 2 else 'README.md'
    print(f"📂 Escaneando directorio: {root}")
    generate_readme(root, output)