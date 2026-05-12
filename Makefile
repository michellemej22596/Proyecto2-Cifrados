BACK_DIR := back
FRONT_DIR := front
VENV_BACK := $(BACK_DIR)/.venv
VENV_FRONT := $(FRONT_DIR)/.venv
PYTHON := python3

.PHONY: help install install-back install-front \
        back front \
        db-reset db-shell \
        test lint clean

help:
	@echo "Comandos disponibles:"
	@echo ""
	@echo "  Setup"
	@echo "    make install        Instala dependencias de back y front"
	@echo "    make install-back   Instala dependencias del backend"
	@echo "    make install-front  Instala dependencias del frontend"
	@echo ""
	@echo "  Ejecución"
	@echo "    make back           Levanta el backend  (http://localhost:8000)"
	@echo "    make front          Levanta el frontend (http://localhost:8501)"
	@echo ""
	@echo "  Base de datos"
	@echo "    make db-reset       Elimina y recrea la base de datos"
	@echo "    make db-shell       Abre una sesión interactiva de SQLite"
	@echo ""
	@echo "  Desarrollo"
	@echo "    make test           Corre los tests del backend"
	@echo "    make clean          Elimina cachés y entornos virtuales"

# ─── Setup ────────────────────────────────────────────────────────────────────

install: install-back install-front

install-back:
	$(PYTHON) -m venv $(VENV_BACK)
	$(VENV_BACK)/bin/pip install --upgrade pip -q
	$(VENV_BACK)/bin/pip install -r $(BACK_DIR)/requirements.txt

install-front:
	$(PYTHON) -m venv $(VENV_FRONT)
	$(VENV_FRONT)/bin/pip install --upgrade pip -q
	$(VENV_FRONT)/bin/pip install -r $(FRONT_DIR)/requirements.txt

# ─── Ejecución ────────────────────────────────────────────────────────────────

back:
	cd $(BACK_DIR) && ../$(VENV_BACK)/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

front:
	cd $(FRONT_DIR) && ../$(VENV_FRONT)/bin/streamlit run app.py --server.port 8501

# ─── Base de datos ────────────────────────────────────────────────────────────

db-reset:
	rm -f $(BACK_DIR)/app.db
	cd $(BACK_DIR) && ../$(VENV_BACK)/bin/python -c "from database import engine, Base; import models; Base.metadata.create_all(bind=engine)"
	@echo "Base de datos recreada en $(BACK_DIR)/app.db"

db-shell:
	sqlite3 $(BACK_DIR)/app.db

# ─── Desarrollo ───────────────────────────────────────────────────────────────

test:
	cd $(BACK_DIR) && ../$(VENV_BACK)/bin/pytest tests/ -v

clean:
	rm -rf $(VENV_BACK) $(VENV_FRONT)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
