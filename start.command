#!/bin/bash
# Запускалка бота. Двойной клик в Finder — і бот працює.

set -e
cd "$(dirname "$0")"

echo "================================"
echo "  UKR/CUKR Bot — запуск"
echo "================================"

# Шукаємо стабільну версію Python (3.12 пріоритет — для неї є готові бібліотеки)
PYTHON=""
for v in python3.12 python3.11 python3.13 python3; do
    if command -v $v &> /dev/null; then
        VER=$($v --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo $VER | cut -d. -f1)
        MINOR=$(echo $VER | cut -d. -f2)
        # Беремо 3.11, 3.12 або 3.13. Для 3.14+ потрібен компілятор — пропускаємо.
        if [ "$MAJOR" = "3" ] && [ "$MINOR" -ge "11" ] && [ "$MINOR" -le "13" ]; then
            PYTHON=$v
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "❌ Не знайдено Python 3.11, 3.12 або 3.13."
    echo ""
    echo "Завантаж Python 3.12 з https://www.python.org/downloads/release/python-31210/"
    echo "(прокрути сторінку вниз, обери macOS 64-bit universal2 installer)"
    echo ""
    read -p "Enter щоб закрити..."
    exit 1
fi

echo "✅ Python: $($PYTHON --version)"

# Якщо venv був створений на іншій версії — перестворити
if [ -d ".venv" ]; then
    VENV_VER=$(.venv/bin/python --version 2>/dev/null || echo "broken")
    CURRENT=$($PYTHON --version)
    if [ "$VENV_VER" != "$CURRENT" ]; then
        echo "🔁 venv від іншої версії Python — перестворюю..."
        rm -rf .venv
    fi
fi

if [ ! -d ".venv" ]; then
    echo "📦 Створюю virtual environment (одноразово)..."
    $PYTHON -m venv .venv
fi

source .venv/bin/activate

echo "📦 Перевіряю залежності (може зайняти хвилину)..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "================================"
echo "  Бот стартує. Логи нижче."
echo "  Зупинити: Ctrl+C"
echo "================================"
echo ""
python bot.py
