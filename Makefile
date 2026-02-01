.PHONY: help backend frontend backend-install frontend-install package

help:
	@echo "Targets:"
	@echo "  backend  - run FastAPI with reload (uv)"
	@echo "  frontend - run Vite dev server"
	@echo "  backend-install  - install backend deps with uv"
	@echo "  frontend-install - install frontend deps"
	@echo "  package  - zip tracked files to ~/flickfeast.zip"

backend:
	uv run uvicorn backend.app.main:app --reload

frontend:
	cd frontend && npm run dev

backend-install:
	uv pip install -r requirements.txt

frontend-install:
	cd frontend && npm install

package:
	git ls-files | zip -@ $(HOME)/flickfeast.zip
