"""The typed route schema: which backend, model and effort each model class runs on.

The driver used to read its classes from the "Model classes" table of `~/.claude/CLAUDE.md`. That table is
still read — it is the legacy config, kept for a transition — but a run may name a route config instead: a
versioned document that says what each class runs on. The schema is strict on purpose: an unknown backend or
an unknown class is an error, never a silent fall back to another billable model.

The schema is a plain dict, so the file format stays a separate question: JSON is read here, YAML when
PyYAML is installed. The rules below are the same either way.
"""

from dataclasses import dataclass
import json
from pathlib import Path

SCHEMA_VERSION = 1
SUPPORTED_VERSIONS = (1,)
CLASSES = ("small", "medium", "large")
BACKENDS = ("claude", "codex")  # the worker backends; pi is lead-only until worker launch is enabled
EFFORTS = ("low", "medium", "high", "xhigh", "max")
ROUTE_FIELDS = ("class", "backend", "model", "effort")
LEGACY_WARNING = ("legacy routing config in use: the 'Model classes' table of %s; it is deprecated and will be "
                  "phased out, pass --routes-file to name the typed route config")


class RouteError(ValueError):
    """The route config is missing, malformed, or names something the driver cannot run."""


@dataclass(frozen=True)
class Route:
    """One model class on one backend. The effort is None when the size/difficulty matrix decides it."""
    klass: str
    backend: str
    model: str
    effort: str = None


@dataclass(frozen=True)
class RouteConfig:
    """A validated route config: its version and the routes it names."""
    version: int
    routes: tuple


def text(value):
    return isinstance(value, str) and bool(value.strip())


def legacy_warning(path):
    """The warning a legacy run gets: the old config still answers, but it is on its way out."""
    return LEGACY_WARNING % path


def validate_route(entry, position):
    """One route of a config, validated. Every failure names the route and the field."""
    if not isinstance(entry, dict):
        raise RouteError("route #%d must be an object" % position)
    unknown = sorted(set(entry) - set(ROUTE_FIELDS))
    if unknown:
        raise RouteError("route #%d has unknown field(s): %s" % (position, ", ".join(unknown)))
    for field in ("class", "backend", "model"):
        if not text(entry.get(field)):
            raise RouteError("route #%d needs a %s" % (position, field))
    klass = entry["class"]
    if klass not in CLASSES:
        raise RouteError("route #%d names the class '%s', which is not a model class (%s)"
                         % (position, klass, ", ".join(CLASSES)))
    backend = entry["backend"]
    if backend not in BACKENDS:
        if backend == "pi":
            raise RouteError("route #%d names the backend 'pi', which cannot run a worker yet (pi is lead-only); "
                             "the worker backends are %s" % (position, ", ".join(BACKENDS)))
        raise RouteError("route #%d names the backend '%s', which is not a worker backend (%s)"
                         % (position, backend, ", ".join(BACKENDS)))
    effort = entry.get("effort")
    if effort is not None and effort not in EFFORTS:
        raise RouteError("route #%d names the effort '%s', which is not an effort (%s)"
                         % (position, effort, ", ".join(EFFORTS)))
    return Route(klass=klass, backend=backend, model=entry["model"].strip(), effort=effort)


def validate(data):
    """The validated route config of a mapping, or a RouteError that says what is wrong with it."""
    if not isinstance(data, dict):
        raise RouteError("the route config must be an object")
    version = data.get("version")
    if version not in SUPPORTED_VERSIONS:
        raise RouteError("the route config version must be %s (got %r)"
                         % (", ".join(map(str, SUPPORTED_VERSIONS)), version))
    unknown = sorted(set(data) - {"version", "routes"})
    if unknown:
        raise RouteError("the route config has unknown field(s): %s" % ", ".join(unknown))
    entries = data.get("routes")
    if not isinstance(entries, list) or not entries:
        raise RouteError("the route config needs a non-empty 'routes' list")
    routes, seen = [], {}
    for position, entry in enumerate(entries, 1):
        route = validate_route(entry, position)
        if route.klass in seen:
            raise RouteError("route #%d repeats the class '%s' (route #%d already names it)"
                             % (position, route.klass, seen[route.klass]))
        seen[route.klass] = position
        routes.append(route)
    return RouteConfig(version=version, routes=tuple(routes))


def load_yaml(raw, path):
    """The mapping a YAML route config holds. YAML needs PyYAML; without it the error says so."""
    try:
        import yaml
    except ImportError:
        raise RouteError("the route config %s is YAML and PyYAML is not installed: install it or use JSON"
                         % path) from None
    try:
        return yaml.safe_load(raw)
    except Exception as error:  # PyYAML raises its own error types
        raise RouteError("the route config %s is not valid YAML: %s" % (path, error)) from None


def load(path):
    """The validated route config of a file. JSON is read; YAML is read when PyYAML is installed."""
    file = Path(path).expanduser()
    try:
        raw = file.read_text(encoding="utf-8")
    except OSError as error:
        raise RouteError("cannot read the route config %s: %s" % (file, error)) from None
    if file.suffix.lower() in (".yaml", ".yml"):
        data = load_yaml(raw, file)
    else:
        try:
            data = json.loads(raw)
        except ValueError as error:
            raise RouteError("the route config %s is not valid JSON: %s" % (file, error)) from None
    return validate(data)


def legacy(backend, models):
    """The routes the legacy 'Model classes' table answers: one model per class, the effort left to the matrix."""
    return {klass: Route(klass=klass, backend=backend, model=model) for klass, model in models.items()}


def resolve(config, backend, legacy_models):
    """The class -> route map a run uses.

    Without a config the legacy table answers, unchanged. With one the config wins, and a class it leaves out
    is an error rather than a silent fall back to another billable model."""
    if config is None:
        return legacy(backend, legacy_models)
    routes = {route.klass: route for route in config.routes}
    missing = [klass for klass in CLASSES if klass not in routes]
    if missing:
        raise RouteError("the route config has no route for the class(es): %s" % ", ".join(missing))
    return routes
