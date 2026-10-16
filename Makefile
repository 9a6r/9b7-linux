.PHONY: test gui-smoke setup builder packages iso-desktop iso-full
test:
	bash scripts/check.sh
gui-smoke:
	QT_QPA_PLATFORM=offscreen .venv/bin/python tests/gui_smoke.py
setup:
	bash scripts/setup-dev.sh
builder:
	docker build -t 9b7-builder -f scripts/builder.Dockerfile .
packages:
	docker run --rm --privileged -v "$(CURDIR):/project" 9b7-builder bash scripts/build-extra-packages.sh
iso-desktop:
	docker run --rm --privileged -v "$(CURDIR):/project" 9b7-builder bash scripts/build-iso.sh desktop
iso-full:
	python3 scripts/bundle-offline.py
	docker run --rm --privileged -v "$(CURDIR):/project" 9b7-builder bash scripts/build-iso.sh full
