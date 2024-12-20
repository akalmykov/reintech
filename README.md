```bash
poetry config virtualenvs.in-project true

poetry env use python3.10

poetry shell

poetry install
```

Installing patched driftpy:

```
poetry add git+https://github.com/PolytonHQ/driftpy.git@bugfix
```
